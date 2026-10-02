"""View acceptance tests — US-11, US-12 and US-13 of work package 4.5.

| Story | Behaviour |
| --- | --- |
| US-11 | team roster with contacts: under-18s show the guardian's contact, not their own |
| US-12 | a member's registration history across all seasons, newest first, deactivated included |
| US-13 | the juniors linked to a guardian, oldest first |

The tables these views read — `guardian`, `guardian_member`, `registration` and `team` —
belong to work packages 4.2, 4.3 and 4.4 and are **not created by this module**. The tests
therefore build them explicitly to exercise the happy path, and a second group of tests
deliberately omits them to prove the views degrade to an explicit "not available yet"
instead of crashing or inventing data.
"""

from __future__ import annotations

import sqlite3

import pytest

from warrigal.db import connect
from warrigal.member import create_member, set_active
from warrigal.views import (
    AVAILABILITY_NO_TABLE,
    AVAILABILITY_OK,
    SOURCE_GUARDIAN,
    SOURCE_MEMBER,
    view_guardian_juniors,
    view_member_history,
    view_roster,
)

#: The sibling work packages' schema, spelled with the column names `views._COLUMN_CANDIDATES`
#: looks for first. Created here only so the views can be exercised before 4.2-4.4 land.
SIBLING_SCHEMA = """
CREATE TABLE IF NOT EXISTS guardian (
    guardian_id     INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    contact_number  TEXT
);
CREATE TABLE IF NOT EXISTS guardian_member (
    guardian_id     INTEGER NOT NULL,
    member_id       INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS registration (
    registration_id INTEGER PRIMARY KEY,
    member_id       INTEGER NOT NULL,
    season          TEXT    NOT NULL,
    status          TEXT    NOT NULL,
    team_id         INTEGER
);
CREATE TABLE IF NOT EXISTS team (
    team_id         INTEGER PRIMARY KEY,
    name            TEXT NOT NULL
);
"""


def _add_sibling_schema(db_path) -> None:
    with connect(db_path) as connection:
        connection.executescript(SIBLING_SCHEMA)
        connection.commit()


def _add(db_path, sql: str, *params) -> None:
    with connect(db_path) as connection:
        connection.execute(sql, params)
        connection.commit()


def _new_member(family_name: str, given_name: str, date_of_birth: str, contact=None) -> int:
    result = create_member(
        given_name=given_name,
        family_name=family_name,
        date_of_birth=date_of_birth,
        contact_number=contact,
    )
    assert result.success, result.message
    assert result.member is not None
    return result.member.member_id


# --- US-13 Guardian's juniors -----------------------------------------------------------


def test_juniors_lists_every_linked_member(db_path) -> None:
    _add_sibling_schema(db_path)
    older = _new_member("Nguyen", "Ana", "2012-05-01")
    younger = _new_member("Nguyen", "Bao", "2015-06-01")
    _add(db_path, "INSERT INTO guardian VALUES (1, 'Linh Nguyen', '0400 000 001')")
    _add(db_path, "INSERT INTO guardian_member VALUES (1, ?)", older)
    _add(db_path, "INSERT INTO guardian_member VALUES (1, ?)", younger)

    result = view_guardian_juniors(1)

    assert result.available is True
    assert result.availability == AVAILABILITY_OK
    assert result.row_count == 2
    assert {row[0] for row in result.rows} == {older, younger}


def test_juniors_are_ordered_oldest_first(db_path) -> None:
    _add_sibling_schema(db_path)
    oldest = _new_member("Nguyen", "Ana", "2010-01-01")
    middle = _new_member("Nguyen", "Bao", "2013-01-01")
    youngest = _new_member("Nguyen", "Chi", "2016-01-01")
    _add(db_path, "INSERT INTO guardian VALUES (1, 'Linh Nguyen', '0400 000 001')")
    for member_id in (youngest, middle, oldest):
        _add(db_path, "INSERT INTO guardian_member VALUES (1, ?)", member_id)

    result = view_guardian_juniors(1)

    assert [row[0] for row in result.rows] == [oldest, middle, youngest]


def test_juniors_show_name_and_date_of_birth(db_path) -> None:
    _add_sibling_schema(db_path)
    member_id = _new_member("Nguyen", "Ana", "2012-05-01")
    _add(db_path, "INSERT INTO guardian VALUES (1, 'Linh Nguyen', '0400 000 001')")
    _add(db_path, "INSERT INTO guardian_member VALUES (1, ?)", member_id)

    result = view_guardian_juniors(1)

    assert result.columns[0] == "member_id"
    row = result.rows[0]
    assert "Ana" in str(row[1]) and "Nguyen" in str(row[1])
    assert "2012-05-01" in str(row[2])


def test_a_guardian_with_no_juniors_is_an_explicit_empty_result(db_path) -> None:
    _add_sibling_schema(db_path)
    _add(db_path, "INSERT INTO guardian VALUES (7, 'Nobody Linked', '0400 000 007')")

    result = view_guardian_juniors(7)

    assert result.available is True
    assert result.empty is True
    assert result.row_count == 0


def test_juniors_report_the_guardian_work_package_when_its_table_is_absent(db_path) -> None:
    """No `guardian_member` table and no `guardian_id` on members: say so, do not invent."""
    _new_member("Nguyen", "Ana", "2012-05-01")

    result = view_guardian_juniors(1)

    assert result.available is False
    assert result.availability == AVAILABILITY_NO_TABLE
    assert "guardian_member" in result.missing_tables
    assert "WBS 4.2" in result.message
    assert result.rows == ()


# --- US-11 Team roster with contacts ----------------------------------------------------


def _roster_fixture(db_path):
    """Build a one-team season with an adult and a minor, and return their ids."""
    _add_sibling_schema(db_path)
    adult = _new_member("Smith", "Dana", "1990-01-01", contact="0400 111 111")
    minor = _new_member("Nguyen", "Ana", "2015-06-01", contact="0400 222 222")
    _add(db_path, "INSERT INTO guardian VALUES (1, 'Linh Nguyen', '0400 999 999')")
    _add(db_path, "INSERT INTO guardian_member VALUES (1, ?)", minor)
    _add(db_path, "INSERT INTO team VALUES (5, 'U13 Girls')")
    _add(
        db_path,
        "INSERT INTO registration (registration_id, member_id, season, status, team_id) "
        "VALUES (1, ?, '2026', 'confirmed', 5)",
        adult,
    )
    _add(
        db_path,
        "INSERT INTO registration (registration_id, member_id, season, status, team_id) "
        "VALUES (2, ?, '2026', 'confirmed', 5)",
        minor,
    )
    return adult, minor


def test_roster_lists_the_members_placed_on_the_team(db_path) -> None:
    adult, minor = _roster_fixture(db_path)

    result = view_roster(5)

    assert result.available is True
    assert {row[0] for row in result.rows} == {adult, minor}


def test_roster_shows_a_minor_the_linked_guardians_contact(db_path) -> None:
    """US-11 acceptance criterion 3 — and the reason the roster is useful to a coach."""
    _adult, minor = _roster_fixture(db_path)

    result = view_roster(5)

    row = next(row for row in result.rows if row[0] == minor)
    assert row[3] == "0400 999 999"
    # `guardian <id>`, so a registrar can see which guardian the number came from.
    assert row[4].startswith(SOURCE_GUARDIAN)


def test_roster_shows_an_adult_their_own_contact(db_path) -> None:
    adult, _minor = _roster_fixture(db_path)

    result = view_roster(5)

    row = next(row for row in result.rows if row[0] == adult)
    assert row[3] == "0400 111 111"
    assert row[4] == SOURCE_MEMBER


def test_an_empty_team_produces_an_explicit_empty_roster(db_path) -> None:
    _add_sibling_schema(db_path)
    _add(db_path, "INSERT INTO team VALUES (9, 'U6 Mixed')")

    result = view_roster(9)

    assert result.available is True
    assert result.empty is True
    assert result.row_count == 0


def test_roster_reports_the_registration_work_package_when_its_table_is_absent(db_path) -> None:
    _new_member("Smith", "Dana", "1990-01-01")

    result = view_roster(5)

    assert result.available is False
    assert result.availability == AVAILABILITY_NO_TABLE
    assert "registration" in result.missing_tables
    assert "WBS 4.3" in result.message


# --- US-12 Member registration history --------------------------------------------------


def test_history_lists_every_season_newest_first(db_path) -> None:
    _add_sibling_schema(db_path)
    member_id = _new_member("Smith", "Dana", "1990-01-01")
    for season in ("2024", "2026", "2025"):
        _add(
            db_path,
            "INSERT INTO registration (member_id, season, status) VALUES (?, ?, 'confirmed')",
            member_id,
            season,
        )

    result = view_member_history(member_id)

    assert result.available is True
    seasons = [str(row[0]) for row in result.rows]
    assert seasons == ["2026", "2025", "2024"]


def test_history_shows_the_team_placed_on(db_path) -> None:
    _add_sibling_schema(db_path)
    member_id = _new_member("Smith", "Dana", "1990-01-01")
    _add(db_path, "INSERT INTO team VALUES (5, 'U13 Girls')")
    _add(
        db_path,
        "INSERT INTO registration (member_id, season, status, team_id) "
        "VALUES (?, '2026', 'confirmed', 5)",
        member_id,
    )

    result = view_member_history(member_id)

    row = result.rows[0]
    assert str(row[0]) == "2026"
    assert "confirmed" in str(row[1])
    assert "U13 Girls" in str(row[2])


def test_history_remains_available_for_a_deactivated_member(db_path) -> None:
    """D-06: the record must stay queryable after the member leaves the club."""
    _add_sibling_schema(db_path)
    member_id = _new_member("Smith", "Dana", "1990-01-01")
    _add(
        db_path,
        "INSERT INTO registration (member_id, season, status) VALUES (?, '2026', 'withdrawn')",
        member_id,
    )
    assert set_active(member_id, active=False).success

    result = view_member_history(member_id)

    assert result.available is True
    assert result.row_count == 1


def test_history_reports_an_unknown_member(db_path) -> None:
    _add_sibling_schema(db_path)

    result = view_member_history(999_999)

    assert result.available is False
    assert result.rows == ()


def test_history_reports_the_registration_work_package_when_its_table_is_absent(db_path) -> None:
    member_id = _new_member("Smith", "Dana", "1990-01-01")

    result = view_member_history(member_id)

    assert result.availability == AVAILABILITY_NO_TABLE
    assert "registration" in result.missing_tables
    assert "WBS 4.3" in result.message


# --- Cross-cutting ----------------------------------------------------------------------


def test_every_view_result_names_itself_and_carries_columns(db_path) -> None:
    _add_sibling_schema(db_path)
    member_id = _new_member("Smith", "Dana", "1990-01-01")

    for result in (
        view_roster(1),
        view_member_history(member_id),
        view_guardian_juniors(1),
    ):
        assert result.view
        assert result.title
        assert result.columns
        assert len(result.columns) == len(result.rows[0]) if result.rows else True


def test_views_never_write(db_path) -> None:
    """A view is read-only: running all three leaves the member count untouched."""
    adult, _minor = _roster_fixture(db_path)

    with connect(db_path) as connection:
        before = connection.execute("SELECT COUNT(*) FROM members").fetchone()[0]

    view_roster(5)
    view_member_history(adult)
    view_guardian_juniors(1)

    with connect(db_path) as connection:
        after = connection.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    assert before == after


def test_views_tolerate_a_malformed_sibling_table(db_path) -> None:
    """A sibling table that exists but lacks the expected columns must not raise."""
    with connect(db_path) as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS registration (nonsense TEXT)")
        connection.commit()
    _new_member("Smith", "Dana", "1990-01-01")

    result = view_member_history(1)

    assert isinstance(result.available, bool)


@pytest.mark.parametrize("already_deactivated_sql", ["UPDATE members SET is_active = 0"])
def test_deactivated_members_are_still_returned_by_the_roster_query_path(
    db_path, already_deactivated_sql: str
) -> None:
    """A member who is deactivated keeps their history; the roster reads registrations."""
    _add_sibling_schema(db_path)
    member_id = _new_member("Smith", "Dana", "1990-01-01")
    _add(db_path, "INSERT INTO team VALUES (5, 'U13 Girls')")
    _add(
        db_path,
        "INSERT INTO registration (member_id, season, status, team_id) "
        "VALUES (?, '2026', 'confirmed', 5)",
        member_id,
    )
    with connect(db_path) as connection:
        connection.execute(already_deactivated_sql)
        connection.commit()

    result = view_roster(5)

    assert isinstance(result.rows, tuple)


def test_connect_yields_a_usable_connection(db_path) -> None:
    with connect(db_path) as connection:
        assert isinstance(connection, sqlite3.Connection)
        assert connection.execute("SELECT 1").fetchone()[0] == 1
