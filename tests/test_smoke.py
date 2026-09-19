"""Smoke tests: the package imports and the CLI entry point runs.

These exist so that the CI workflow has something real to run before Sprint 1 code lands.
Replace them with behaviour tests as each story is completed (WBS 5.1-5.2).
"""

from warrigal import __version__
from warrigal.__main__ import build_parser


def test_version_is_declared() -> None:
    assert __version__


def test_parser_has_a_help_message() -> None:
    parser = build_parser()
    assert "Warrigal Park FC" in parser.description


def test_main_returns_zero() -> None:
    from warrigal.__main__ import main

    assert main([]) == 0
