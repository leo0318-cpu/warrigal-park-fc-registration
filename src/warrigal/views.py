"""Read-only views: team roster with contacts, registration history, guardian's juniors.

Three stories live here (WBS 4.5):

- **US-11 Team roster with contacts** — every member currently placed on a team, with the
  *guardian's* contact details shown in place of the member's own for anyone under 18.
- **US-12 Member registration history** — every registration a member holds, across all
  seasons, most recent season first, still available for a deactivated member.
- **US-13 Guardian's juniors** — every member linked to a guardian, oldest first.

The `guardian`, `registration` and `team` tables are created by *other* work packages and may
not exist yet. Every view therefore does two things before answering:

1. checks that the tables it needs are present (`db.table_exists`), and
2. reads the column names it actually finds (`db.table_columns`) instead of assuming a shape.

A missing table produces an explicit "not available yet" result naming the work package that
owns it — never a crash and never invented data. Nothing in this module writes to the
database: every statement is a SELECT.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any, Callable, Sequence

from warrigal.db import connect, season_start, table_columns, table_exists
from warrigal.member import (
    Member,
    adult_age,
    blank_to_none,
    member_from_row,
    requires_linked_guardian,
)

__all__ = [
    "AVAILABILITY_NO_TABLE",
    "AVAILABILITY_OK",
    "AVAILABILITY_PARTIAL",
    "ViewResult",
    "resolve_guardian_contact",
    "view_guardian_juniors",
    "view_member_history",
    "view_roster",
]

#: The view answered from tables that all exist.
AVAILABILITY_OK = "available"
#: The view answered, but a related table that would enrich it does not exist yet.
AVAILABILITY_PARTIAL = "partial"
#: The view cannot answer because the table it needs does not exist yet.
AVAILABILITY_NO_TABLE = "not_available"

#: Who owns each table that this module reads but never creates (WBS 4.2-4.4).
_OWNERS = {
    "guardian": "WBS 4.2 (guardian links)",
    "guardians": "WBS 4.2 (guardian links)",
    "guardian_member": "WBS 4.2 (guardian links)",
    "member_guardian": "WBS 4.2 (guardian links)",
    "guardian_link": "WBS 4.2 (guardian links)",
    "registration": "WBS 4.3 (season registration)",
    "registrations": "WBS 4.3 (season registration)",
    "team": "WBS 4.4 (team roster)",
    "teams": "WBS 4.4 (team roster)",
}

#: Candidate table names for each relationship, tried in order. The name actually used is
#: discovered at run time because the sibling work packages are still being written.
_GUARDIAN_TABLES = ("guardian", "guardians")
_REGISTRATION_TABLES = ("registration", "registrations")
_TEAM_TABLES = ("team", "teams")
_LINK_TABLES = ("guardian_member", "member_guardian", "guardian_link")

#: Candidate column names for each value the views need. The first one present wins, so a
#: sibling work package may spell a column differently without breaking the view.
_COLUMN_CANDIDATES: dict[str, tuple[str, ...]] = {
    "member_id": ("member_id", "id"),
    "given_name": ("given_name", "first_name"),
    "family_name": ("family_name", "last_name", "surname"),
    "date_of_birth": ("date_of_birth", "dob"),
    "contact_number": ("contact_number", "contact", "phone", "phone_number", "mobile"),
    "is_active": ("is_active", "active"),
    "guardian_id": ("guardian_id", "id"),
    "link_member_id": ("member_id",),
    "link_guardian_id": ("guardian_id",),
    "registration_id": ("registration_id", "id"),
    "season": ("season", "season_year", "season_id"),
    "status": ("status", "registration_status"),
    "team_id": ("team_id",),
    "team_name": ("name", "team_name", "title"),
}

#: How the source of a roster row's contact details is described.
SOURCE_MEMBER = "member"
SOURCE_GUARDIAN = "guardian"


@dataclass(frozen=True)
class ViewResult:
    """The outcome of one view.

    `available` says whether the view could answer at all, and `availability` distinguishes a
    complete answer from one that is missing detail because another work package's table is
    not there yet. `missing_tables` names what is absent — so the registrar is told exactly
    which work package to wait for — and `notes` explains anything else the answer leaves out.
    """

    view: str
    title: str
    columns: tuple[str, ...] = ()
    rows: tuple[tuple[Any, ...], ...] = ()
    available: bool = True
    availability: str = AVAILABILITY_OK
    message: str = ""
    missing_tables: tuple[str, ...] = ()
    notes: tuple[str, ...] = field(default=())

    @property
    def empty(self) -> bool:
        """Return whether the view answered with no rows."""
        return self.available and not self.rows

    @property
    def row_count(self) -> int:
        """Return how many rows the view returned."""
        return len(self.rows)


# --- Discovery of the sibling work packages' schema -------------------------------------


def _pick(columns: Sequence[str], key: str) -> str | None:
    """Return the column in `columns` matching the given candidate group, or `None`."""
    lowered = {column.lower(): column for column in columns}
    for candidate in _COLUMN_CANDIDATES.get(key, ()):
        if candidate in lowered:
            return lowered[candidate]
    return None


def _owner(table: str) -> str:
    """Return a human-readable owner for a table name."""
    return _OWNERS.get(table, "another work package")


def _first_existing_table(
    connection: sqlite3.Connection, candidates: Sequence[str]
) -> str | None:
    """Return the first of the candidate table names that exists in this database."""
    for name in candidates:
        if table_exists(connection, name):
            return name
    return None


def _not_available(
    *, view: str, title: str, missing: str, columns: tuple[str, ...]
) -> ViewResult:
    """Build the explicit "not available yet" answer a view gives for a missing table."""
    return ViewResult(
        view=view,
        title=title,
        columns=columns,
        rows=(),
        available=False,
        availability=AVAILABILITY_NO_TABLE,
        missing_tables=(missing,),
        message=(
            f"{title} is not available yet: the '{missing}' table does not exist in this "
            f"database. It is created by {_owner(missing)}, which is not in this branch yet. "
            "No rows are shown and nothing has been invented; run this view again once that "
            "work package has created its table."
        ),
    )


def _registration_columns(
    connection: sqlite3.Connection, table: str
) -> dict[str, str | None]:
    """Return the registration columns that could be resolved, or `{}` if unusable."""
    columns = table_columns(connection, table)
    resolved = {
        "member_id": _pick(columns, "member_id"),
        "registration_id": _pick(columns, "registration_id"),
        "season": _pick(columns, "season"),
        "status": _pick(columns, "status"),
        "team_id": _pick(columns, "team_id"),
    }
    if resolved["member_id"] is None:
        return {}
    return resolved


def _id_sort_key(value: Any) -> str:
    """Return a text key that sorts identifiers numerically without failing on text."""
    if value is None:
        return ""
    text = str(value)
    return text.zfill(20) if text.isdigit() else f"~{text}"


def _team_name_resolver(
    connection: sqlite3.Connection,
) -> Callable[[Any], str | None] | None:
    """Return a callable that turns a team id into a team name, or `None` when impossible.

    The `team` table belongs to WBS 4.4. When it is absent, or has no name column, the roster
    and the history still answer — they just cannot put a name against the team id.
    """
    team_table = _first_existing_table(connection, _TEAM_TABLES)
    if team_table is None:
        return None
    columns = table_columns(connection, team_table)
    name_column = _pick(columns, "team_name")
    lowered = {column.lower(): column for column in columns}
    id_column = lowered.get("team_id") or lowered.get("id")
    if name_column is None or id_column is None:
        return None

    cache: dict[Any, str | None] = {}

    def resolve(team_id: Any) -> str | None:
        if team_id is None:
            return None
        if team_id not in cache:
            row = connection.execute(
                f'SELECT "{name_column}" FROM "{team_table}" WHERE "{id_column}" = ?',
                (team_id,),
            ).fetchone()
            cache[team_id] = str(row[0]) if row is not None and row[0] is not None else None
        return cache[team_id]

    return resolve


def _guardians_for_members(
    connection: sqlite3.Connection, member_ids: Sequence[int]
) -> tuple[dict[int, int], list[str]]:
    """Return `{member_id: guardian_id}` and any notes about what could not be read.

    The member/guardian link is WBS 4.2's. Two plausible shapes are supported: a link table
    (`guardian_member` / `member_guardian` / `guardian_link`) and a `guardian_id` column on
    the member row. Both are read when both exist — the link table wins, because that is the
    shape the decision log describes for siblings sharing one guardian (D-05).
    """
    if not member_ids:
        return {}, []

    notes: list[str] = []
    found: dict[int, int] = {}
    link_table = _first_existing_table(connection, _LINK_TABLES)
    if link_table is not None:
        columns = table_columns(connection, link_table)
        member_column = _pick(columns, "link_member_id")
        guardian_column = _pick(columns, "link_guardian_id")
        if member_column and guardian_column:
            placeholders = ", ".join("?" for _ in member_ids)
            rows = connection.execute(
                f'SELECT "{member_column}", "{guardian_column}" FROM "{link_table}" '
                f'WHERE "{member_column}" IN ({placeholders})',
                list(member_ids),
            ).fetchall()
            for row in rows:
                if row[0] is not None and row[1] is not None:
                    found[int(row[0])] = int(row[1])
        else:
            notes.append(
                f"The '{link_table}' table exists but has no recognizable member/guardian "
                "columns, so it was not read."
            )

    member_columns = table_columns(connection, "members")
    direct_column = _pick(member_columns, "guardian_id")
    if direct_column:
        placeholders = ", ".join("?" for _ in member_ids)
        rows = connection.execute(
            f'SELECT member_id, "{direct_column}" FROM members '
            f'WHERE member_id IN ({placeholders}) AND "{direct_column}" IS NOT NULL',
            list(member_ids),
        ).fetchall()
        for row in rows:
            found.setdefault(int(row[0]), int(row[1]))
    return found, notes


def _guardian_contact(connection: sqlite3.Connection, guardian_id: int) -> str | None:
    """Return a guardian's contact number, or `None` when the table or the value is absent."""
    guardian_table = _first_existing_table(connection, _GUARDIAN_TABLES)
    if guardian_table is None:
        return None
    columns = table_columns(connection, guardian_table)
    contact_column = _pick(columns, "contact_number")
    lowered = {column.lower(): column for column in columns}
    id_column = lowered.get("guardian_id") or lowered.get("id")
    if contact_column is None or id_column is None:
        return None
    row = connection.execute(
        f'SELECT "{contact_column}" FROM "{guardian_table}" WHERE "{id_column}" = ?',
        (guardian_id,),
    ).fetchone()
    if row is None:
        return None
    return blank_to_none(str(row[0]) if row[0] is not None else None)


# --- US-11 Team roster with contacts ----------------------------------------------------


def resolve_guardian_contact(
    member: Member,
    *,
    guardian_id: int | None,
    guardian_contact: str | None,
    on: date,
    has_guardian_table: bool = True,
    adult_age_limit: int | None = None,
) -> tuple[str | None, str]:
    """Decide whose contact details a roster row shows: `(contact_number, source)`.

    This is the under-18 rule of US-11. A member who is under 18 at the season start must
    show the linked guardian's details; an adult shows their own. The `source` text says
    which was used, so a registrar can see why a number looks unexpected:

    | source | meaning |
    | --- | --- |
    | `member` | the member is an adult: their own number is shown |
    | `guardian <id>` | under 18 and the guardian's number is shown instead |
    | `guardian <id>: no contact recorded` | under 18, guardian linked, no number held |
    | `member (no guardian linked)` | under 18 but WBS 4.2 has linked no guardian yet |
    | `member (guardian table not available yet - WBS 4.2)` | the link cannot be read at all |

    Nothing is invented: when the guardian's number is unknown the row says so rather than
    silently falling back to the junior's own number, because a junior's own number may not
    be the number the club should be ringing.
    """
    limit = adult_age() if adult_age_limit is None else adult_age_limit
    if not requires_linked_guardian(member.date_of_birth, season_start=on, adult_age=limit):
        return member.contact_number, SOURCE_MEMBER

    if guardian_id is None:
        if has_guardian_table:
            return member.contact_number, "member (no guardian linked)"
        return member.contact_number, "member (guardian table not available yet - WBS 4.2)"
    if guardian_contact is None:
        return None, f"guardian {guardian_id}: no contact recorded"
    return guardian_contact, f"guardian {guardian_id}"


def view_roster(
    team_id: int | None = None, *, connection: sqlite3.Connection | None = None
) -> ViewResult:
    """List the members currently placed on a team, with contact details.

    Each row shows the member's name, date of birth and a contact number: the member's own
    for an adult, the linked guardian's for a member who is under 18 at the season start.
    An empty team is an explicit empty roster, not an error.

    Placement is WBS 4.4's data. When its table (or WBS 4.3's) does not exist, this returns a
    "not available yet" result naming that work package.
    """

    def _work(connection: sqlite3.Connection) -> ViewResult:
        title = "Team roster with contacts"
        columns = ("member_id", "name", "date_of_birth", "contact_number", "contact_source")

        registration_table = _first_existing_table(connection, _REGISTRATION_TABLES)
        if registration_table is None:
            return _not_available(
                view="roster", title=title, missing="registration", columns=columns
            )

        resolved = _registration_columns(connection, registration_table)
        if not resolved:
            return ViewResult(
                view="roster",
                title=title,
                columns=columns,
                available=False,
                availability=AVAILABILITY_NO_TABLE,
                missing_tables=(registration_table,),
                message=(
                    f"{title} is not available yet: the '{registration_table}' table exists "
                    "but has no recognizable member column, so no placement can be read. "
                    "Nothing has been invented."
                ),
            )

        where = ""
        params: list[Any] = []
        if team_id is not None:
            if not resolved["team_id"]:
                return ViewResult(
                    view="roster",
                    title=title,
                    columns=columns,
                    available=False,
                    availability=AVAILABILITY_NO_TABLE,
                    missing_tables=(registration_table,),
                    message=(
                        f"{title} is not available yet: the '{registration_table}' table has "
                        "no team column, so one team's roster cannot be read."
                    ),
                )
            where = f' WHERE r."{resolved["team_id"]}" = ?'
            params.append(team_id)

        selection = [f'r."{resolved["member_id"]}" AS member_id']
        if resolved["team_id"]:
            selection.append(f'r."{resolved["team_id"]}" AS team_id')
        placed_rows = connection.execute(
            f'SELECT {", ".join(selection)} FROM "{registration_table}" r{where}',
            params,
        ).fetchall()

        placement: dict[int, Any] = {}
        for row in placed_rows:
            member_id = row["member_id"]
            if member_id is None:
                continue
            placement.setdefault(int(member_id), row["team_id"] if "team_id" in row.keys() else None)

        label = f"team {team_id}" if team_id is not None else "any team"
        if not placement:
            return ViewResult(
                view="roster",
                title=title,
                columns=columns,
                rows=(),
                message=(
                    f"The roster for {label} is empty: no member is currently placed on a "
                    "team. That is an empty roster, not an error."
                ),
            )

        member_columns = table_columns(connection, "members")
        name_column = _pick(member_columns, "given_name")
        family_column = _pick(member_columns, "family_name")
        dob_column = _pick(member_columns, "date_of_birth")
        active_column = _pick(member_columns, "is_active")
        contact_column = _pick(member_columns, "contact_number")
        if not (name_column and family_column and dob_column):
            return ViewResult(
                view="roster",
                title=title,
                columns=columns,
                available=False,
                availability=AVAILABILITY_NO_TABLE,
                missing_tables=("members",),
                message=(
                    f"{title} is not available yet: the member register has no recognizable "
                    "name and date-of-birth columns."
                ),
            )

        selected = (
            f'member_id, "{name_column}", "{family_column}", "{dob_column}"'
            + (f', "{active_column}"' if active_column else "")
            + (f', "{contact_column}"' if contact_column else "")
        )
        placeholders = ", ".join("?" for _ in placement)
        member_rows = connection.execute(
            f"SELECT {selected} FROM members WHERE member_id IN ({placeholders})",
            list(placement),
        ).fetchall()
        members: dict[int, Member] = {}
        for row in member_rows:
            members[int(row[0])] = member_from_row(
                {
                    "member_id": row[0],
                    "given_name": row[1],
                    "family_name": row[2],
                    "date_of_birth": row[3],
                    "is_active": row[4] if active_column else 1,
                    # The member's own number is needed for US-11: an adult on the roster
                    # shows it. Omitting it here made every adult row read as blank.
                    "contact_number": row[5] if contact_column else None,
                }
            )

        guardian_links, notes = _guardians_for_members(connection, list(placement))
        has_guardian_table = _first_existing_table(connection, _GUARDIAN_TABLES) is not None
        team_lookup = _team_name_resolver(connection)
        on = season_start()
        limit = adult_age()

        missing_tables: list[str] = []
        if not has_guardian_table and guardian_links == {}:
            missing_tables.append("guardian")
        if team_lookup is None and any(value is not None for value in placement.values()):
            missing_tables.append("team")

        roster_rows: list[tuple[Any, ...]] = []
        for member_id in sorted(
            (mid for mid in placement if mid in members),
            key=lambda mid: (
                members[mid].family_name.lower(),
                members[mid].given_name.lower(),
                members[mid].date_of_birth,
            ),
        ):
            member = members[member_id]
            if not member.is_active:
                # A deactivated member cannot be placed on a team (US-04). A stale row is
                # reported rather than silently dropped.
                notes.append(
                    f"Member {member.member_id}, {member.full_name}, is deactivated but still "
                    "appears on a roster row; deactivated members cannot be placed on a team."
                )
                continue
            guardian_id = guardian_links.get(member.member_id)
            contact, source = resolve_guardian_contact(
                member,
                guardian_id=guardian_id,
                guardian_contact=(
                    _guardian_contact(connection, guardian_id)
                    if guardian_id is not None
                    else None
                ),
                on=on,
                has_guardian_table=has_guardian_table,
                adult_age_limit=limit,
            )
            roster_rows.append(
                (
                    member.member_id,
                    member.full_name,
                    member.date_of_birth.isoformat(),
                    contact or "",
                    source,
                )
            )

        for member_id in sorted(mid for mid in placement if mid not in members):
            notes.append(
                f"A registration row refers to member_id {member_id}, which is not in the "
                "member register; the row is reported rather than hidden."
            )
            roster_rows.append(
                (member_id, f"(member {member_id} not found)", "unknown", "", "unknown")
            )

        if "guardian" in missing_tables:
            notes.append(
                "The 'guardian' table does not exist yet (WBS 4.2), so no guardian contact "
                "details can be shown."
            )
        if "team" in missing_tables:
            notes.append(
                "The 'team' table does not exist yet (WBS 4.4), so team names cannot be "
                "shown; the placed members are still listed."
            )

        return ViewResult(
            view="roster",
            title=title,
            columns=columns,
            rows=tuple(roster_rows),
            availability=AVAILABILITY_PARTIAL if missing_tables else AVAILABILITY_OK,
            missing_tables=tuple(missing_tables),
            notes=tuple(dict.fromkeys(notes)),
            message=(
                f"{len(roster_rows)} member(s) currently placed on a team ({label})."
                if roster_rows
                else f"The roster for {label} is empty: no placed member is still active."
            ),
        )

    if connection is not None:
        return _work(connection)
    with connect() as owned:
        return _work(owned)


# --- US-12 Member registration history --------------------------------------------------


def view_member_history(
    member_id: int, *, connection: sqlite3.Connection | None = None
) -> ViewResult:
    """List every registration a member holds, across all seasons, newest season first.

    Each entry shows the season, the status and the team placed on (if any). The view is
    read-only and deliberately works for a deactivated member: registration history has to
    survive for insurance and audit purposes (D-06).
    """

    def _work(connection: sqlite3.Connection) -> ViewResult:
        columns = ("season", "status", "team")
        row = connection.execute(
            "SELECT member_id, given_name, family_name, date_of_birth, contact_number, "
            "is_active FROM members WHERE member_id = ?",
            (member_id,),
        ).fetchone()
        if row is None:
            return ViewResult(
                view="history",
                title="Member registration history",
                columns=columns,
                available=False,
                availability=AVAILABILITY_NO_TABLE,
                message=(
                    "Member registration history is not available: there is no member with "
                    f"member_id {member_id}. Nothing was found and nothing was invented."
                ),
            )
        member = member_from_row(row)
        title = f"Registration history for member {member.member_id}, {member.full_name}"

        registration_table = _first_existing_table(connection, _REGISTRATION_TABLES)
        if registration_table is None:
            return _not_available(
                view="history", title=title, missing="registration", columns=columns
            )

        resolved = _registration_columns(connection, registration_table)
        if not resolved:
            return ViewResult(
                view="history",
                title=title,
                columns=columns,
                available=False,
                availability=AVAILABILITY_NO_TABLE,
                missing_tables=(registration_table,),
                message=(
                    f"{title} is not available yet: the '{registration_table}' table exists "
                    "but has no recognizable member column."
                ),
            )

        selection = [f'r."{resolved["member_id"]}" AS member_id']
        for key in ("season", "status", "team_id", "registration_id"):
            if resolved[key]:
                selection.append(f'r."{resolved[key]}" AS {key}')
        rows = connection.execute(
            f'SELECT {", ".join(selection)} FROM "{registration_table}" r '
            f'WHERE r."{resolved["member_id"]}" = ?',
            (member_id,),
        ).fetchall()

        team_lookup = _team_name_resolver(connection)
        missing_tables: list[str] = []
        notes: list[str] = []
        if team_lookup is None:
            missing_tables.append("team")
            notes.append(
                "The 'team' table does not exist yet (WBS 4.4), so the team placed on cannot "
                "be named; each registration's season and status are complete."
            )

        entries: list[tuple[str, str, Any, Any]] = []
        for row in rows:
            keys = row.keys()
            season_value = row["season"] if "season" in keys else None
            if season_value is None:
                season_value = season_start().year
            status_value = row["status"] if "status" in keys else None
            team_value = row["team_id"] if "team_id" in keys else None
            registration_value = row["registration_id"] if "registration_id" in keys else None
            entries.append(
                (str(season_value), _id_sort_key(registration_value), status_value, team_value)
            )

        # Most recent season first. Seasons are zero-padded years in practice, so descending
        # text order is descending season order; the registration id breaks ties within a
        # season so the order is stable rather than arbitrary.
        entries.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)

        history_rows: list[tuple[Any, ...]] = []
        for season_value, _registration_key, status_value, team_value in entries:
            if team_value is None:
                team_label = "(not placed on a team)"
            elif team_lookup is None:
                team_label = f"(team {team_value}; name unavailable)"
            else:
                looked_up = team_lookup(team_value)
                team_label = looked_up or f"(unknown team {team_value})"
            history_rows.append(
                (
                    season_value,
                    status_value if status_value is not None else "(no status recorded)",
                    team_label,
                )
            )

        if history_rows:
            message = (
                f"{len(history_rows)} registration(s) held by member {member.member_id}, "
                f"{member.full_name}, most recent season first."
            )
        else:
            message = (
                f"No registrations are held by member {member.member_id}, {member.full_name}. "
                "That is an empty history, not an error."
            )
        if not member.is_active:
            notes.append(
                "This member is deactivated; the history is still shown because the record "
                "and its registrations are never deleted (Decision Log D-06)."
            )

        return ViewResult(
            view="history",
            title=title,
            columns=columns,
            rows=tuple(history_rows),
            availability=AVAILABILITY_PARTIAL if missing_tables else AVAILABILITY_OK,
            missing_tables=tuple(missing_tables),
            notes=tuple(notes),
            message=message,
        )

    if connection is not None:
        return _work(connection)
    with connect() as owned:
        return _work(owned)


# --- US-13 Guardian's juniors -----------------------------------------------------------


def view_guardian_juniors(
    guardian_id: int, *, connection: sqlite3.Connection | None = None
) -> ViewResult:
    """List every member linked to a guardian, oldest first.

    Each entry shows the member's name, date of birth and current registration status. The
    current status is the newest season's status when WBS 4.3's table is available, and an
    explicit "not available yet" when it is not. A guardian with no linked members produces
    an explicit empty result, not an error.
    """

    def _work(connection: sqlite3.Connection) -> ViewResult:
        title = f"Juniors linked to guardian {guardian_id}"
        columns = ("member_id", "name", "date_of_birth", "registration_status")

        link_table = _first_existing_table(connection, _LINK_TABLES)
        member_columns = table_columns(connection, "members")
        direct_column = _pick(member_columns, "guardian_id")
        if link_table is None and not direct_column:
            result = _not_available(
                view="juniors",
                title=title,
                missing="guardian_member",
                columns=columns,
            )
            return replace(
                result,
                message=(
                    "Juniors linked to a guardian is not available yet: neither a "
                    "member/guardian link table nor a guardian_id column on the member "
                    "register exists in this database. The link is created by "
                    f"{_owner('guardian_member')}, which is not in this branch yet. "
                    "No rows are shown and nothing has been invented; run this view again "
                    "once that work package has created its table."
                ),
            )

        member_ids: set[int] = set()
        notes: list[str] = []
        if link_table is not None:
            link_columns = table_columns(connection, link_table)
            member_column = _pick(link_columns, "link_member_id")
            guardian_column = _pick(link_columns, "link_guardian_id")
            if member_column and guardian_column:
                rows = connection.execute(
                    f'SELECT "{member_column}" FROM "{link_table}" '
                    f'WHERE "{guardian_column}" = ?',
                    (guardian_id,),
                ).fetchall()
                member_ids.update(int(row[0]) for row in rows if row[0] is not None)
            else:
                notes.append(
                    f"The '{link_table}' table exists but has no recognizable member/guardian "
                    "columns, so it was not read."
                )
        if direct_column:
            rows = connection.execute(
                f'SELECT member_id FROM members WHERE "{direct_column}" = ?', (guardian_id,)
            ).fetchall()
            member_ids.update(int(row[0]) for row in rows if row[0] is not None)

        member_ids.discard(0)
        if not member_ids:
            return ViewResult(
                view="juniors",
                title=title,
                columns=columns,
                rows=(),
                notes=tuple(notes),
                message=(
                    f"Guardian {guardian_id} has no linked members. That is an empty result, "
                    "not an error."
                ),
            )

        placeholders = ", ".join("?" for _ in member_ids)
        member_rows = connection.execute(
            "SELECT member_id, given_name, family_name, date_of_birth, contact_number, "
            f"is_active FROM members WHERE member_id IN ({placeholders})",
            list(member_ids),
        ).fetchall()
        members = [member_from_row(row) for row in member_rows]
        # Oldest first: at the desk the oldest junior is usually the one being dealt with.
        members.sort(key=lambda item: (item.date_of_birth, item.member_id))

        registration_table = _first_existing_table(connection, _REGISTRATION_TABLES)
        statuses: dict[int, str] = {}
        missing_tables: list[str] = []
        if registration_table is None:
            missing_tables.append("registration")
            notes.append(
                "The 'registration' table does not exist yet (WBS 4.3), so the current "
                "registration status cannot be shown for any linked member."
            )
        else:
            resolved = _registration_columns(connection, registration_table)
            if not resolved:
                missing_tables.append(registration_table)
                notes.append(
                    f"The '{registration_table}' table exists but has no recognizable member "
                    "column, so no status could be read."
                )
            else:
                selection = [f'r."{resolved["member_id"]}" AS member_id']
                for key in ("season", "status", "registration_id"):
                    if resolved[key]:
                        selection.append(f'r."{resolved[key]}" AS {key}')
                rows = connection.execute(
                    f'SELECT {", ".join(selection)} FROM "{registration_table}" r '
                    f'WHERE r."{resolved["member_id"]}" IN ({placeholders})',
                    list(member_ids),
                ).fetchall()
                newest: dict[int, tuple[str, str]] = {}
                for row in rows:
                    keys = row.keys()
                    mid = int(row["member_id"])
                    season_value = row["season"] if "season" in keys else None
                    season_key = str(season_value) if season_value is not None else ""
                    status_value = row["status"] if "status" in keys else None
                    registration_key = _id_sort_key(
                        row["registration_id"] if "registration_id" in keys else None
                    )
                    candidate = (season_key, registration_key)
                    if mid not in newest or candidate > newest[mid]:
                        newest[mid] = candidate
                        statuses[mid] = (
                            str(status_value)
                            if status_value is not None
                            else "(no status recorded)"
                        )

        junior_rows = tuple(
            (
                member.member_id,
                member.full_name,
                member.date_of_birth.isoformat(),
                statuses.get(member.member_id, "(registration status not available yet)"),
            )
            for member in members
        )

        return ViewResult(
            view="juniors",
            title=title,
            columns=columns,
            rows=junior_rows,
            availability=AVAILABILITY_PARTIAL if missing_tables else AVAILABILITY_OK,
            missing_tables=tuple(missing_tables),
            notes=tuple(notes),
            message=(
                f"{len(junior_rows)} member(s) are linked to guardian {guardian_id}, "
                "oldest first."
                if junior_rows
                else f"Guardian {guardian_id} has no linked members."
            ),
        )

    if connection is not None:
        return _work(connection)
    with connect() as owned:
        return _work(owned)
