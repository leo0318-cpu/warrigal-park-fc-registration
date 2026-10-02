"""Command-line entry point.

Usage:
    python -m warrigal --help
    python -m warrigal --version
    python -m warrigal member add --given-name Ana --family-name Nguyen --date-of-birth 2015-06-01
    python -m warrigal member find --family-name nguyen
    python -m warrigal member show 1
    python -m warrigal member update 1 --contact-number 0400 000 000
    python -m warrigal member deactivate 1
    python -m warrigal member reactivate 1
    python -m warrigal view roster
    python -m warrigal view roster 5
    python -m warrigal view history 1
    python -m warrigal view juniors 1

The member commands are WBS 4.1 and the read-only views are WBS 4.5. Guardians (4.2),
season registrations (4.3) and team rosters (4.4) are added by their own work packages; until
they land, a view that needs their table says so instead of guessing.

Every command prints a human-readable line and exits with a status a volunteer can act on:

| Exit | Meaning |
| --- | --- |
| 0 | the command succeeded (an empty search result or an empty roster is a success) |
| 2 | the command was refused — bad arguments, a validation error, or a view whose table is not there yet |
| 3 | a possible duplicate was found and nothing was saved; repeat with `--confirm-duplicate` |
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Sequence

from warrigal import __version__
from warrigal.member import (
    Member,
    OperationResult,
    can_be_placed_on_roster,
    create_member,
    find_by_family_name,
    get_member,
    set_active,
    update_member,
)
from warrigal.views import (
    ViewResult,
    view_guardian_juniors,
    view_member_history,
    view_roster,
)

EXIT_OK = 0
EXIT_REFUSED = 2
EXIT_NEEDS_CONFIRMATION = 3


# --- Printing ---------------------------------------------------------------------------


def _print_member(member: Member, *, width: int = 4) -> None:
    """Print one member as two aligned lines a registrar can read at the desk."""
    state = "active" if member.is_active else "deactivated"
    print(f"{'id':<{width}}: {member.member_id}")
    print(f"{'name':<{width}}: {member.full_name}")
    print(f"{'born':<{width}}: {member.date_of_birth.isoformat()}")
    print(f"{'contact':<{width}}: {member.contact_number or '(none recorded)'}")
    print(f"{'state':<{width}}: {state}")


def _print_members(members: Sequence[Member]) -> None:
    """Print a list of members, one block each, never merging same-named people."""
    for index, member in enumerate(members, start=1):
        print(f"[{index}]")
        _print_member(member)


def _report(result: OperationResult) -> int:
    """Print the outcome of an operation and return the process exit status."""
    for warning in result.warnings:
        if warning:
            print(f"warning: {warning}", file=sys.stderr)
    if result.message:
        print(result.message)
    if result.success:
        if result.member is not None and not result.members:
            _print_member(result.member)
        elif result.members:
            _print_members(result.members)
        return EXIT_OK
    if result.requires_confirmation:
        return EXIT_NEEDS_CONFIRMATION
    return EXIT_REFUSED


def _cell(value: Any) -> str:
    """Render one table cell, treating a missing value as an empty cell."""
    return "" if value is None else str(value)


def _print_view_result(result: ViewResult) -> int:
    """Print one view: its title, the table, then any message and notes.

    A view that cannot answer because another work package's table is missing exits with
    `EXIT_REFUSED`; an empty but answerable view exits with `EXIT_OK`, because an empty
    roster is a fact, not a failure.
    """
    # A "not available yet" message already leads with the title; printing both would
    # repeat the same sentence twice.
    if not result.message.startswith(result.title):
        print(result.title)
    if result.rows:
        widths = [len(column) for column in result.columns]
        for row in result.rows:
            for index, cell in enumerate(row[: len(widths)]):
                widths[index] = max(widths[index], len(_cell(cell)))
        header = "  ".join(column.ljust(widths[i]) for i, column in enumerate(result.columns))
        print(header)
        print("-" * len(header))
        for row in result.rows:
            print(
                "  ".join(
                    _cell(cell).ljust(widths[i]) for i, cell in enumerate(row[: len(widths)])
                )
            )
    if result.message:
        print(result.message)
    for note in result.notes:
        print(f"note: {note}")
    return EXIT_OK if result.available else EXIT_REFUSED


def _refuse_id(raw: str, kind: str) -> int:
    """Report an identifier that is not a whole number and refuse the command."""
    print(
        f"'{raw}' is not a {kind} id. Ids are whole numbers, for example 12.",
        file=sys.stderr,
    )
    return EXIT_REFUSED


# --- Parser -----------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="warrigal",
        description="Warrigal Park FC member registration and team roster system.",
    )
    parser.add_argument("--version", action="version", version=f"warrigal {__version__}")
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")

    member_parser = subparsers.add_parser(
        "member", help="create, find, show, update and deactivate members (WBS 4.1)"
    )
    member_commands = member_parser.add_subparsers(dest="member_command", metavar="<action>")

    add_parser = member_commands.add_parser("add", help="create a member")
    add_parser.add_argument("--given-name", required=True, help="the member's given name")
    add_parser.add_argument("--family-name", required=True, help="the member's family name")
    add_parser.add_argument(
        "--date-of-birth",
        required=True,
        help="date of birth as YYYY-MM-DD or DD/MM/YYYY; must be a real date, not in the future",
    )
    add_parser.add_argument("--contact-number", default=None, help="optional contact number")
    add_parser.add_argument(
        "--confirm-duplicate",
        action="store_true",
        help="save even though an active member already has this name and date of birth",
    )

    find_parser = member_commands.add_parser(
        "find", help="find members by whole or partial family name"
    )
    find_parser.add_argument("--family-name", required=True, help="whole or partial family name")
    find_parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="also return deactivated members",
    )

    show_parser = member_commands.add_parser("show", help="show one member by id")
    show_parser.add_argument("member_id", help="the system-generated member id")

    update_parser = member_commands.add_parser("update", help="change a member's details")
    update_parser.add_argument("member_id", help="the system-generated member id")
    update_parser.add_argument("--given-name", default=None, help="new given name")
    update_parser.add_argument("--family-name", default=None, help="new family name")
    update_parser.add_argument("--date-of-birth", default=None, help="new date of birth")
    update_parser.add_argument("--contact-number", default=None, help="new contact number")
    update_parser.add_argument(
        "--clear-contact-number",
        action="store_true",
        help="remove the stored contact number",
    )
    update_parser.add_argument(
        "--confirm-duplicate",
        action="store_true",
        help="save even though another active member has this name and date of birth",
    )

    for action, help_text in (
        ("deactivate", "deactivate a member instead of deleting the record (D-06)"),
        ("reactivate", "restore a deactivated member, history intact"),
    ):
        state_parser = member_commands.add_parser(action, help=help_text)
        state_parser.add_argument("member_id", help="the system-generated member id")

    roster_parser = member_commands.add_parser(
        "roster-check", help="report whether a member may be placed on a team roster"
    )
    roster_parser.add_argument("member_id", help="the system-generated member id")

    view_parser = subparsers.add_parser(
        "view", help="read-only views: roster, registration history, a guardian's juniors (WBS 4.5)"
    )
    view_commands = view_parser.add_subparsers(dest="view_command", metavar="<view>")

    view_roster_parser = view_commands.add_parser(
        "roster", help="list the members placed on a team, with contact details"
    )
    view_roster_parser.add_argument(
        "team_id",
        nargs="?",
        default=None,
        help="the team id; omit to list every placement across all teams",
    )

    view_history_parser = view_commands.add_parser(
        "history", help="list one member's registrations across all seasons, newest first"
    )
    view_history_parser.add_argument("member_id", help="the system-generated member id")

    view_juniors_parser = view_commands.add_parser(
        "juniors", help="list the members linked to a guardian, oldest first"
    )
    view_juniors_parser.add_argument("guardian_id", help="the guardian id")

    return parser


# --- Dispatch ---------------------------------------------------------------------------


def _parse_member_id(raw: str) -> int | None:
    """Return a member id from command-line text, or `None` when it is not a whole number."""
    text = raw.strip()
    if not text.isdigit():
        return None
    return int(text)


def _run_member_command(args: argparse.Namespace) -> int:
    """Execute one `member` subcommand."""
    command = args.member_command
    if command is None:
        build_parser().parse_args(["member", "--help"])
        return EXIT_REFUSED

    if command == "add":
        return _report(
            create_member(
                given_name=args.given_name,
                family_name=args.family_name,
                date_of_birth=args.date_of_birth,
                contact_number=args.contact_number,
                confirm_duplicate=args.confirm_duplicate,
            )
        )

    if command == "find":
        return _report(
            find_by_family_name(
                args.family_name, include_inactive=args.include_inactive
            )
        )

    member_id = _parse_member_id(args.member_id)
    if member_id is None:
        print(
            f"'{args.member_id}' is not a member id. Member ids are whole numbers, "
            "for example 12.",
            file=sys.stderr,
        )
        return EXIT_REFUSED

    if command == "show":
        result = get_member(member_id)
        if result.success and result.member is not None:
            print(result.message)
            _print_member(result.member)
            return EXIT_OK
        for error in result.errors:
            print(f"error: {error}", file=sys.stderr)
        print(result.message, file=sys.stderr)
        return EXIT_REFUSED

    if command == "update":
        return _report(
            update_member(
                member_id,
                given_name=args.given_name,
                family_name=args.family_name,
                date_of_birth=args.date_of_birth,
                contact_number=args.contact_number,
                clear_contact_number=args.clear_contact_number,
                confirm_duplicate=args.confirm_duplicate,
            )
        )

    if command == "deactivate":
        return _report(set_active(member_id, False))

    if command == "reactivate":
        return _report(set_active(member_id, True))

    if command == "roster-check":  # pragma: no cover - defensive
        return _report(can_be_placed_on_roster(member_id))

    build_parser().parse_args(["member", "--help"])  # pragma: no cover - defensive
    return EXIT_REFUSED


def _run_view_command(args: argparse.Namespace) -> int:
    """Execute one `view` subcommand (WBS 4.5)."""
    command = args.view_command
    if command is None:
        build_parser().parse_args(["view", "--help"])
        return EXIT_REFUSED

    if command == "history":
        member_id = _parse_member_id(args.member_id)
        if member_id is None:
            return _refuse_id(args.member_id, "member")
        return _print_view_result(view_member_history(member_id))

    if command == "juniors":
        guardian_id = _parse_member_id(args.guardian_id)
        if guardian_id is None:
            return _refuse_id(args.guardian_id, "guardian")
        return _print_view_result(view_guardian_juniors(guardian_id))

    if command == "roster":
        if args.team_id is None:
            return _print_view_result(view_roster())
        team_id = _parse_member_id(args.team_id)
        if team_id is None:
            return _refuse_id(args.team_id, "team")
        return _print_view_result(view_roster(team_id))

    build_parser().parse_args(["view", "--help"])  # pragma: no cover - defensive
    return EXIT_REFUSED


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "member":
        return _run_member_command(args)
    if args.command == "view":
        return _run_view_command(args)

    parser.print_help()
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
