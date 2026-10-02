"""SQLite connection handling, schema creation and settings (WBS 4.1).

Persistence is deliberately boring: the charter fixes the budget at $0 (constraint 3.3) and
the deliverable as a Python command-line application, so the standard library's `sqlite3`
module satisfies both the economic and the technical constraint with nothing to procure
(design note `docs/dev/4.1-member-crud-design.md`, decision 4).

Two settings are read from the environment — both are documented in `config.env.template`:

| Variable | Default | Meaning |
| --- | --- | --- |
| `WARRIGAL_DB_PATH` | `data/warrigal.db` | SQLite database file, created on first run |
| `WARRIGAL_SEASON_START` | `03-01` | date (MM-DD) a season is treated as starting |

No credential and no absolute path is hard-coded: every path either comes from the
environment or is resolved relative to the current working directory.

The schema is created idempotently (`CREATE TABLE IF NOT EXISTS`), so a clean checkout runs
with no separate setup step (Definition of Done criterion 5). Migrations are recorded in
`schema_migrations`; each migration is applied once and may be re-run safely.
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path

__all__ = [
    "DEFAULT_DB_PATH",
    "DEFAULT_SEASON_START",
    "SCHEMA_VERSION",
    "connect",
    "database_path",
    "initialise",
    "season_start",
    "table_exists",
    "table_columns",
    "MIGRATIONS",
]

#: Where the database lives when `WARRIGAL_DB_PATH` is unset.
DEFAULT_DB_PATH = "data/warrigal.db"

#: The date a season is treated as starting when `WARRIGAL_SEASON_START` is unset (MM-DD).
DEFAULT_SEASON_START = "03-01"

#: Schema version this code expects; raise it when a migration is appended.
SCHEMA_VERSION = 1


# --- The member register ----------------------------------------------------------------
#
# `member_id` is INTEGER PRIMARY KEY AUTOINCREMENT: the system generates it, the user never
# supplies it, and AUTOINCREMENT guarantees an identifier is never handed out twice even
# after the table's high-water mark changes (US-01 acceptance criterion 3).
#
# Dates are stored as ISO-8601 text (`YYYY-MM-DD`) — SQLite has no date type, ISO text sorts
# and compares correctly, and the file stays readable for audit purposes (D-06).
#
# `contact_number` is nullable: the club holds only the personal data it needs (charter,
# minors' privacy).
_MEMBERS_TABLE = """
CREATE TABLE IF NOT EXISTS members (
    member_id       INTEGER PRIMARY KEY AUTOINCREMENT CHECK (member_id > 0),
    given_name      TEXT    NOT NULL,
    family_name     TEXT    NOT NULL,
    date_of_birth   TEXT    NOT NULL,
    contact_number  TEXT,
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
)
"""

# Search is by partial family name and must never collapse people who share a name, so the
# index is on the family name only; identical names are separated by date of birth (US-01
# acceptance criterion 2, design note decision 1).
_MEMBERS_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_members_family_name ON members (family_name)",
    "CREATE INDEX IF NOT EXISTS idx_members_name_dob "
    "ON members (given_name, family_name, date_of_birth)",
)

#: Ordered migrations. Append new statements here and raise `SCHEMA_VERSION`; a migration
#: that has already been recorded is skipped, so applying them repeatedly is safe.
MIGRATIONS: tuple[tuple[int, str, tuple[str, ...]], ...] = (
    (1, "create the member register", (_MEMBERS_TABLE, *_MEMBERS_INDEXES)),
)

_MIGRATION_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
)
"""


def database_path() -> Path:
    """Return the database file the application should use.

    `WARRIGAL_DB_PATH` wins when it is set; otherwise the path falls back to
    `data/warrigal.db` relative to the current working directory. A relative value is kept
    relative to the working directory rather than to this file, so the setting behaves the
    same whether the package is run from a checkout or installed.
    """
    configured = os.environ.get("WARRIGAL_DB_PATH", "").strip()
    return Path(configured or DEFAULT_DB_PATH)


def season_start() -> date:
    """Return the date on which the current season is treated as starting.

    Read from `WARRIGAL_SEASON_START` as `MM-DD` (assumption A-01: a player's age is
    measured at the season start, not at the current date). An unparseable value falls back
    to the documented default of 1 March rather than stopping the application, because a
    typo in a local settings file must not make the register unusable at the desk.
    """
    raw = os.environ.get("WARRIGAL_SEASON_START", "").strip() or DEFAULT_SEASON_START
    try:
        month, day = raw.split("-")
        # Year 2000 is a leap year, so 02-29 parses.
        candidate = date(2000, int(month), int(day))
    except (ValueError, TypeError):
        month, day = DEFAULT_SEASON_START.split("-")
        candidate = date(2000, int(month), int(day))
    return date(date.today().year, candidate.month, candidate.day)


@contextmanager
def connect(path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    """Open a connection to the register, creating the file and its schema if needed.

    The connection is committed on success and rolled back on error, so a failed operation
    never leaves a half-written record behind. Row access is by column name.
    """
    db_path = Path(path) if path is not None else database_path()
    if db_path.parent != Path(""):
        db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        initialise(connection)
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialise(connection: sqlite3.Connection) -> None:
    """Create the schema and apply any migration this database has not seen yet."""
    with closing(connection.cursor()) as cursor:
        cursor.execute(_MIGRATION_TABLE)
        applied = {
            int(row[0])
            for row in cursor.execute("SELECT version FROM schema_migrations").fetchall()
        }
        for version, description, statements in MIGRATIONS:
            if version in applied:
                continue
            for statement in statements:
                cursor.execute(statement)
            cursor.execute(
                "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                (version, description),
            )
    connection.commit()


def table_exists(connection: sqlite3.Connection, name: str) -> bool:
    """Return whether a table (or view) of that name exists in this database.

    Tables belonging to the other work packages — `guardian`, `registration`, `team` —
    are created by their owners and may be absent. Every caller must handle `False`
    rather than assume the table is there (WBS 4.5 graceful degradation).
    """
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?",
        (name,),
    ).fetchone()
    return row is not None


def table_columns(connection: sqlite3.Connection, name: str) -> tuple[str, ...]:
    """Return the column names of a table, or an empty tuple when it does not exist.

    The sibling work packages are still being written, so the views read the column names
    they actually find rather than assuming a shape. `PRAGMA table_info` takes no
    parameters and the table name is whitespace-stripped before use, so no caller-supplied
    text reaches the statement.
    """
    if not table_exists(connection, name):
        return ()
    safe_name = name.replace("'", "").replace('"', "").strip()
    rows = connection.execute(f'PRAGMA table_info("{safe_name}")').fetchall()
    return tuple(str(row[1]) for row in rows)
