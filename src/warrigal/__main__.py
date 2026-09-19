"""Command-line entry point.

Usage:
    python -m warrigal --help
    python -m warrigal --version

The command surface for members, guardians, registrations and rosters is added in
Sprint 1 (WBS 4.1-4.2) and Sprint 2 (WBS 4.3-4.5). This entry point exists so that the
"clean checkout runs from the README alone" criterion is verifiable from day one.
"""

from __future__ import annotations

import argparse

from warrigal import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="warrigal",
        description="Warrigal Park FC member registration and team roster system.",
    )
    parser.add_argument("--version", action="version", version=f"warrigal {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
