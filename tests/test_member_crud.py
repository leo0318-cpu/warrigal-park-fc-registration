"""Member CRUD acceptance tests — US-01 to US-04 of work package 4.1.

These are the four stories the work package exists to satisfy:

| Story | Behaviour |
| --- | --- |
| US-01 | create a member: generated id, validated date of birth, duplicate warning |
| US-02 | find by partial family name: all matches, case-insensitive, deactivated excluded |
| US-03 | update any editable field; unknown id changes nothing; the id never changes |
| US-04 | deactivate instead of delete; record and history stay retrievable; reactivate |

Every test runs against the throwaway database from `conftest.py`, so the developer's own
`data/warrigal.db` is never touched.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta

import pytest

from warrigal import member as member_module
from warrigal.db import connect
from warrigal.member import (
    adult_age,
    age_at,
    can_be_placed_on_roster,
    create_member,
    find_by_family_name,
    get_member,
    is_senior,
    parse_date_of_birth,
    requires_linked_guardian,
    set_active,
    update_member,
)


def _yesterday() -> str:
    """Return yesterday's date as ISO text — always a valid date of birth."""
    return (date.today() - timedelta(days=1)).isoformat()


# --- Age and the under-18 boundary ------------------------------------------------------


def test_age_counts_a_birthday_falling_on_the_date() -> None:
    assert age_at(date(2008, 3, 1), date(2026, 3, 1)) == 18
    assert age_at(date(2008, 3, 1), date(2026, 2, 28)) == 17


def test_birthday_on_the_season_start_counts_as_adult() -> None:
    """CONTRIBUTING example: treat the 18th birthday falling on the season start as adult."""
    assert is_senior(date(2008, 3, 1), date(2026, 3, 1)) is True


def test_birthday_one_day_after_the_season_start_is_still_a_minor() -> None:
    assert is_senior(date(2008, 3, 2), date(2026, 3, 1)) is False
    assert requires_linked_guardian(date(2008, 3, 2), season_start=date(2026, 3, 1)) is True


def test_requires_linked_guardian_on_both_sides_of_the_boundary(
    minor_date_of_birth: date, adult_date_of_birth: date, season_start_date: date
) -> None:
    assert minor_date_of_birth == adult_date_of_birth + timedelta(days=1)
    assert requires_linked_guardian(minor_date_of_birth, season_start=season_start_date) is True
    assert requires_linked_guardian(adult_date_of_birth, season_start=season_start_date) is False


def test_adult_age_defaults_to_eighteen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WARRIGAL_ADULT_AGE", raising=False)
    assert adult_age() == 18


def test_adult_age_is_read_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WARRIGAL_ADULT_AGE", "21")
    assert adult_age() == 21
    assert is_senior(date(2008, 3, 1), date(2026, 3, 1), adult_age=adult_age()) is False


def test_unreadable_adult_age_falls_back_to_the_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WARRIGAL_ADULT_AGE", "eighteen")
    assert adult_age() == 18


# --- US-01 Create a member --------------------------------------------------------------


def test_create_member_stores_every_field(db_path) -> None:
    result = create_member(
        given_name="Ana",
        family_name="Nguyen",
        date_of_birth="2015-06-01",
        contact_number="0400 111 222",
    )
    assert result.success, result.message
    assert result.changed is True
    assert result.member is not None
    assert result.member.member_id > 0
    assert result.member.full_name == "Ana Nguyen"
    assert result.member.date_of_birth == date(2015, 6, 1)
    assert result.member.contact_number == "0400 111 222"
    assert result.member.is_active is True


def test_create_member_accepts_dd_mm_yyyy_from_a_paper_form(db_path) -> None:
    """The club writes dates day-first on paper; both spellings are accepted."""
    result = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="01/06/2015"
    )
    assert result.success, result.message
    assert result.member is not None
    assert result.member.date_of_birth == date(2015, 6, 1)


def test_contact_number_is_optional(db_path) -> None:
    result = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert result.success, result.message
    assert result.member is not None
    assert result.member.contact_number is None


def test_generated_ids_are_unique_and_not_reused(db_path) -> None:
    first = create_member(given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01")
    second = create_member(given_name="Binh", family_name="Nguyen", date_of_birth="2016-02-02")
    assert first.member is not None and second.member is not None
    assert first.member.member_id != second.member.member_id
    reused = first.member.member_id

    # Deactivation does not free the identifier, so it can never be handed out again.
    assert set_active(reused, False).success
    third = create_member(given_name="Chi", family_name="Nguyen", date_of_birth="2017-03-03")
    assert third.member is not None
    assert third.member.member_id not in {first.member.member_id, second.member.member_id}


def test_create_member_survives_a_restart(db_path) -> None:
    """A second connection sees the record: persistence is on disk, not in memory."""
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None

    with connect(db_path) as reopened:
        row = reopened.execute(
            "SELECT given_name, family_name, date_of_birth FROM members WHERE member_id = ?",
            (created.member.member_id,),
        ).fetchone()
    assert row is not None
    assert tuple(row) == ("Ana", "Nguyen", "2015-06-01")


def test_creating_a_duplicate_warns_before_saving(db_path) -> None:
    first = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert first.success

    duplicate = create_member(
        given_name="ana", family_name="nguyen", date_of_birth="2015-06-01"
    )
    assert duplicate.success is False
    assert duplicate.requires_confirmation is True
    assert "Possible duplicate" in duplicate.message
    assert str(first.member.member_id) in duplicate.message
    assert duplicate.member is None

    found = find_by_family_name("Nguyen")
    assert len(found.members) == 1, "the refused duplicate must not have been written"


def test_duplicate_can_be_confirmed_and_saved(db_path) -> None:
    create_member(given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01")
    confirmed = create_member(
        given_name="Ana",
        family_name="Nguyen",
        date_of_birth="2015-06-01",
        confirm_duplicate=True,
    )
    assert confirmed.success, confirmed.message
    assert confirmed.warnings and "Possible duplicate" in confirmed.warnings[0]
    assert len(find_by_family_name("Nguyen").members) == 2


def test_same_name_with_a_different_date_of_birth_is_not_a_duplicate(db_path) -> None:
    create_member(given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01")
    second = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2016-07-02"
    )
    assert second.success, second.message
    assert second.warnings == ()


def test_deactivated_member_is_not_a_duplicate(db_path) -> None:
    """A deactivated record is history, not a duplicate (D-06)."""
    first = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert first.member is not None
    assert set_active(first.member.member_id, False).success

    again = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert again.success, again.message
    assert again.warnings == ()


# --- US-01 validation -------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_date",
    ["2025-02-30", "31/02/2015", "not a date", "2015-13-01", ""],
)
def test_impossible_dates_of_birth_are_refused(db_path, bad_date: str) -> None:
    result = create_member(given_name="Ana", family_name="Nguyen", date_of_birth=bad_date)
    assert result.success is False
    assert "date_of_birth" in result.message


def test_a_future_date_of_birth_is_refused(db_path) -> None:
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    result = create_member(given_name="Ana", family_name="Nguyen", date_of_birth=tomorrow)
    assert result.success is False
    assert "future" in result.message
    assert find_by_family_name("Nguyen").members == ()


def test_every_missing_required_field_is_reported_in_one_message(db_path) -> None:
    """US-01 acceptance criterion 4: one round trip, all problems named."""
    result = create_member(given_name="", family_name="   ", date_of_birth=None)
    assert result.success is False
    assert "given_name" in result.message
    assert "family_name" in result.message
    assert "date_of_birth" in result.message
    assert set(result.errors) == {
        "given_name is required",
        "family_name is required",
        "date_of_birth is required",
    }
    with connect(db_path) as connection:
        stored = connection.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    assert stored == 0, "validation must reject the whole record, not part of it"


def test_a_missing_field_and_a_bad_date_are_reported_together(db_path) -> None:
    result = create_member(given_name="", family_name="Nguyen", date_of_birth="2025-02-30")
    assert result.success is False
    assert "given_name is required" in result.message
    assert "not a real calendar date" in result.message


def test_names_are_stored_without_surrounding_whitespace(db_path) -> None:
    result = create_member(
        given_name="  Ana  ", family_name="  Nguyen  ", date_of_birth="2015-06-01"
    )
    assert result.success, result.message
    assert result.member is not None
    assert result.member.given_name == "Ana"
    assert result.member.family_name == "Nguyen"


def test_parse_date_of_birth_reports_the_two_failure_modes_separately() -> None:
    assert parse_date_of_birth("2025-02-30")[1] is not None
    assert "real calendar date" in parse_date_of_birth("2025-02-30")[1]
    assert parse_date_of_birth("2015-06-01")[0] == date(2015, 6, 1)


# --- US-02 Find by name -----------------------------------------------------------------


def _three_nguyens() -> list[int]:
    """Create three members who share a family name; return their ids."""
    ids: list[int] = []
    for given_name, date_of_birth in (
        ("Ana", "2015-06-01"),
        ("Binh", "2014-04-04"),
        ("Chi", "2016-08-08"),
    ):
        result = create_member(
            given_name=given_name, family_name="Nguyen", date_of_birth=date_of_birth
        )
        assert result.success, result.message
        assert result.member is not None
        ids.append(result.member.member_id)
    return ids


def test_partial_family_name_returns_every_match(db_path) -> None:
    ids = _three_nguyens()
    result = find_by_family_name("ngu")
    assert result.success, result.message
    assert {member.member_id for member in result.members} == set(ids)


def test_search_is_case_insensitive(db_path) -> None:
    _three_nguyens()
    assert len(find_by_family_name("NGUYEN").members) == 3
    assert len(find_by_family_name("nGuYeN").members) == 3


def test_same_name_members_are_returned_separately_with_their_dates_of_birth(db_path) -> None:
    """The 2024 incident: two players with one name must never be collapsed into one row."""
    first = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    second = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2016-07-02"
    )
    assert first.member and second.member

    result = find_by_family_name("Nguyen")
    assert len(result.members) == 2
    assert {member.member_id for member in result.members} == {
        first.member.member_id,
        second.member.member_id,
    }
    assert {member.date_of_birth for member in result.members} == {
        date(2015, 6, 1),
        date(2016, 7, 2),
    }


def test_search_excludes_deactivated_members_by_default(db_path) -> None:
    ids = _three_nguyens()
    assert set_active(ids[0], False).success

    default_result = find_by_family_name("Nguyen")
    assert {member.member_id for member in default_result.members} == set(ids[1:])
    assert all(member.is_active for member in default_result.members)


def test_search_can_include_deactivated_members_on_request(db_path) -> None:
    ids = _three_nguyens()
    assert set_active(ids[0], False).success

    result = find_by_family_name("Nguyen", include_inactive=True)
    assert {member.member_id for member in result.members} == set(ids)
    assert any(not member.is_active for member in result.members)
    assert result.warnings and "deactivated" in result.warnings[0].lower()


def test_no_match_is_an_explicit_empty_result_not_an_error(db_path) -> None:
    _three_nguyens()
    result = find_by_family_name("Smith")
    assert result.success is True
    assert result.members == ()
    assert "No members match" in result.message
    assert result.errors == ()


def test_search_refuses_an_empty_search_term(db_path) -> None:
    result = find_by_family_name("   ")
    assert result.success is False
    assert "family_name is required" in result.message


def test_show_returns_a_member_by_id(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None
    shown = get_member(created.member.member_id)
    assert shown.success, shown.message
    assert shown.member == created.member


def test_show_reports_an_unknown_id(db_path) -> None:
    result = get_member(4242)
    assert result.success is False
    assert "No member with member_id 4242" in result.message
    assert result.member is None


# --- US-03 Update -----------------------------------------------------------------------


def test_update_changes_an_editable_field_and_persists_it(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None

    result = update_member(created.member.member_id, contact_number="0400 999 000")
    assert result.success, result.message
    assert result.member is not None
    assert result.member.contact_number == "0400 999 000"

    with connect(db_path) as reopened:
        stored = reopened.execute(
            "SELECT contact_number FROM members WHERE member_id = ?",
            (created.member.member_id,),
        ).fetchone()[0]
    assert stored == "0400 999 000"


def test_update_can_change_several_fields_at_once(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None
    result = update_member(
        created.member.member_id,
        given_name="Anastasia",
        family_name="Tran",
        date_of_birth="2015-07-07",
    )
    assert result.success, result.message
    assert result.member is not None
    assert (result.member.given_name, result.member.family_name) == ("Anastasia", "Tran")
    assert result.member.date_of_birth == date(2015, 7, 7)


def test_update_leaves_untouched_fields_alone(db_path) -> None:
    created = create_member(
        given_name="Ana",
        family_name="Nguyen",
        date_of_birth="2015-06-01",
        contact_number="0400 111 222",
    )
    assert created.member is not None
    result = update_member(created.member.member_id, given_name="Anastasia")
    assert result.success, result.message
    assert result.member is not None
    assert result.member.contact_number == "0400 111 222"
    assert result.member.date_of_birth == date(2015, 6, 1)


def test_update_validates_the_date_of_birth(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None
    member_id = created.member.member_id

    future = update_member(member_id, date_of_birth=(date.today() + timedelta(days=2)).isoformat())
    assert future.success is False
    assert "future" in future.message

    impossible = update_member(member_id, date_of_birth="2015-02-30")
    assert impossible.success is False
    assert "not a real calendar date" in impossible.message

    unchanged = get_member(member_id)
    assert unchanged.member is not None
    assert unchanged.member.date_of_birth == date(2015, 6, 1)


def test_update_reports_every_missing_field_at_once(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None
    result = update_member(created.member.member_id, given_name="", family_name="")
    assert result.success is False
    assert "given_name is required" in result.message
    assert "family_name is required" in result.message


def test_update_of_a_non_existent_member_changes_nothing(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None

    result = update_member(9999, given_name="Ghost")
    assert result.success is False
    assert "no member with member_id 9999" in result.message
    assert result.changed is False

    survivors = find_by_family_name("Nguyen")
    assert len(survivors.members) == 1
    assert survivors.members[0].given_name == "Ana"


def test_update_never_changes_the_identifier(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None
    member_id = created.member.member_id

    result = update_member(member_id, family_name="Tran", contact_number="0400 000 000")
    assert result.success, result.message
    assert result.member is not None
    assert result.member.member_id == member_id
    assert str(member_id) in result.message

    with connect(db_path) as reopened:
        ids = [row[0] for row in reopened.execute("SELECT member_id FROM members")]
    assert ids == [member_id]


def test_update_warns_when_it_would_create_a_duplicate(db_path) -> None:
    first = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    second = create_member(
        given_name="Binh", family_name="Tran", date_of_birth="2015-06-01"
    )
    assert first.member and second.member

    warning = update_member(
        second.member.member_id, given_name="Ana", family_name="Nguyen"
    )
    assert warning.success is False
    assert warning.requires_confirmation is True
    assert "Possible duplicate" in warning.message
    # Nothing changed: the member is still Binh Tran.
    still = get_member(second.member.member_id)
    assert still.member is not None
    assert still.member.given_name == "Binh"

    confirmed = update_member(
        second.member.member_id,
        given_name="Ana",
        family_name="Nguyen",
        confirm_duplicate=True,
    )
    assert confirmed.success, confirmed.message
    assert len(find_by_family_name("Nguyen").members) == 2


def test_update_can_clear_the_contact_number(db_path) -> None:
    created = create_member(
        given_name="Ana",
        family_name="Nguyen",
        date_of_birth="2015-06-01",
        contact_number="0400 111 222",
    )
    assert created.member is not None
    result = update_member(created.member.member_id, clear_contact_number=True)
    assert result.success, result.message
    assert result.member is not None
    assert result.member.contact_number is None


def test_update_with_no_changes_is_not_an_error(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None
    result = update_member(created.member.member_id)
    assert result.success is True
    assert result.changed is False
    assert "Nothing to update" in result.message


# --- US-04 Deactivate instead of delete --------------------------------------------------


def test_deactivate_keeps_the_record_queryable_by_id(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None
    member_id = created.member.member_id

    result = set_active(member_id, False)
    assert result.success, result.message
    assert result.member is not None
    assert result.member.is_active is False

    still_there = get_member(member_id)
    assert still_there.success, still_there.message
    assert still_there.member is not None
    assert still_there.member.is_active is False
    assert still_there.member.full_name == "Ana Nguyen"

    with connect(db_path) as reopened:
        count = reopened.execute(
            "SELECT COUNT(*) FROM members WHERE member_id = ?", (member_id,)
        ).fetchone()[0]
    assert count == 1, "the row is deactivated, never deleted (D-06)"


def test_deactivated_members_are_excluded_from_the_active_list(db_path) -> None:
    ids = _three_nguyens()
    assert set_active(ids[0], False).success
    remaining = find_by_family_name("Nguyen")
    assert ids[0] not in {member.member_id for member in remaining.members}
    assert all(member.is_active for member in remaining.members)


def test_a_deactivated_member_cannot_be_placed_on_a_team_roster(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None
    member_id = created.member.member_id

    assert can_be_placed_on_roster(member_id).success is True

    assert set_active(member_id, False).success
    blocked = can_be_placed_on_roster(member_id)
    assert blocked.success is False
    assert "deactivated" in blocked.message
    assert "cannot be placed on a team roster" in blocked.message


def test_reactivating_restores_the_member_with_history_intact(db_path) -> None:
    created = create_member(
        given_name="Ana",
        family_name="Nguyen",
        date_of_birth="2015-06-01",
        contact_number="0400 111 222",
    )
    assert created.member is not None
    member_id = created.member.member_id
    created_at = created.member.created_at

    assert set_active(member_id, False).success
    back = set_active(member_id, True)
    assert back.success, back.message
    assert back.member is not None
    assert back.member.is_active is True
    assert back.member.contact_number == "0400 111 222"
    assert back.member.created_at == created_at, "the record was not recreated"

    assert can_be_placed_on_roster(member_id).success is True
    assert member_id in {member.member_id for member in find_by_family_name("Nguyen").members}


def test_repeating_a_state_change_is_not_an_error(db_path) -> None:
    created = create_member(
        given_name="Ana", family_name="Nguyen", date_of_birth="2015-06-01"
    )
    assert created.member is not None
    member_id = created.member.member_id

    assert set_active(member_id, False).success
    again = set_active(member_id, False)
    assert again.success is True
    assert again.changed is False
    assert "already deactivated" in again.message

    assert set_active(member_id, True).success
    again_active = set_active(member_id, True)
    assert again_active.success is True
    assert again_active.changed is False
    assert "already active" in again_active.message


def test_state_change_on_an_unknown_member_changes_nothing(db_path) -> None:
    result = set_active(31337, False)
    assert result.success is False
    assert "no member with member_id 31337" in result.message
    assert can_be_placed_on_roster(31337).success is False


# --- Schema behaviour -------------------------------------------------------------------


def test_schema_creation_is_idempotent(db_path) -> None:
    """Opening the database twice must not fail or duplicate the schema."""
    with connect(db_path) as first:
        first.execute(
            "INSERT INTO members (given_name, family_name, date_of_birth) VALUES (?, ?, ?)",
            ("Ana", "Nguyen", "2015-06-01"),
        )
    with connect(db_path) as second:
        versions = [row[0] for row in second.execute("SELECT version FROM schema_migrations")]
        count = second.execute("SELECT COUNT(*) FROM members").fetchone()[0]
    assert versions == [1]
    assert count == 1


def test_member_table_rejects_a_negative_identifier(
    connection: sqlite3.Connection,
) -> None:
    """The identifier is generated by the system; the schema does not invite user values."""
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO members (member_id, given_name, family_name, date_of_birth) "
            "VALUES (?, ?, ?, ?)",
            (-1, "Ana", "Nguyen", "2015-06-01"),
        )


def test_the_module_exposes_the_guardian_requirement_helper() -> None:
    """The under-18 rule is reachable from the member side for WBS 4.3 and 4.4."""
    assert member_module.requires_linked_guardian(date(2015, 6, 1), season_start=date(2026, 3, 1))
