"""Command-line interface for logstats."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__
from .parser import parse_lines
from .render import render_json, render_table
from .stats import build_report


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        prog="logstats",
        description=(
            "Parse Common/Combined Log Format access logs and print analytics."
        ),
    )
    parser.add_argument(
        "logfile",
        nargs="?",
        default="-",
        help="Path to the access log, or '-' for stdin (default: stdin).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable table.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        metavar="N",
        help="Number of top IPs/URLs/minutes to show (default: 5).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _open_source(logfile: str):
    if logfile == "-":
        return sys.stdin
    return open(logfile, encoding="utf-8", errors="replace")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.top < 1:
        parser.error("--top must be >= 1")

    try:
        source = _open_source(args.logfile)
    except OSError as exc:
        print(f"logstats: cannot open {args.logfile!r}: {exc}", file=sys.stderr)
        return 2

    try:
        entries, skipped = parse_lines(source)
    finally:
        if source is not sys.stdin:
            source.close()

    report = build_report(entries, skipped=skipped, top=args.top)

    if args.json:
        print(render_json(report))
    else:
        print(render_table(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
