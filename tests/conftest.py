"""Shared fixtures for the test suite (WBS 5.1-5.2).

Every test runs against its own SQLite file under pytest's `tmp_path`, and the member and
view modules are told about it through `WARRIGAL_DB_PATH`. No test may touch the developer's
`data/warrigal.db`: a test suite that writes to the real register is worse than no test
suite.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import date, timedelta
from pathlib import Path

import pytest

from warrigal.db import connect, season_start


@pytest.fixture
def db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the application at a throwaway database and yield its path.

    `WARRIGAL_SEASON_START` is pinned to the documented default so the age-boundary tests do
    not change meaning when a developer has a local value in `config.env`.
    """
    path = tmp_path / "warrigal-test.db"
    monkeypatch.setenv("WARRIGAL_DB_PATH", str(path))
    monkeypatch.setenv("WARRIGAL_SEASON_START", "03-01")
    monkeypatch.delenv("WARRIGAL_ADULT_AGE", raising=False)
    return path


@pytest.fixture
def connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    """Yield an open connection to the throwaway database, schema already created."""
    with connect(db_path) as open_connection:
        yield open_connection


@pytest.fixture
def season_start_date() -> date:
    """Return the season start the fixtures assume (1 March of the current year)."""
    return season_start()


@pytest.fixture
def minor_date_of_birth(season_start_date: date) -> date:
    """Return a date of birth that is a minor on the season start by exactly one day.

    The under-18 boundary case: the member turns 18 the day *after* the season starts.
    """
    try:
        eighteenth = season_start_date.replace(year=season_start_date.year - 18)
    except ValueError:  # 29 February season start in a non-leap year
        eighteenth = season_start_date.replace(
            year=season_start_date.year - 18, day=28
        )
    return eighteenth + timedelta(days=1)


@pytest.fixture
def adult_date_of_birth(season_start_date: date) -> date:
    """Return a date of birth that is an adult on the season start by exactly one day.

    The other side of the boundary: the member turns 18 *on* the season start.
    """
    try:
        return season_start_date.replace(year=season_start_date.year - 18)
    except ValueError:  # pragma: no cover - only for a 29 February season start
        return season_start_date.replace(year=season_start_date.year - 18, day=28)
