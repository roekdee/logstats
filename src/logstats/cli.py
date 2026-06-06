"""Command-line interface for logstats."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__
from .parser import filter_entries, parse_lines, parse_time_bound
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
        "--since",
        metavar="WHEN",
        help=(
            "Only count lines at or after this time. Accepts an ISO date "
            "(2000-10-10) or datetime (2000-10-10T13:57)."
        ),
    )
    parser.add_argument(
        "--until",
        metavar="WHEN",
        help=(
            "Only count lines at or before this time (inclusive). Same "
            "format as --since."
        ),
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
        since = parse_time_bound(args.since) if args.since else None
        until = parse_time_bound(args.until) if args.until else None
    except ValueError as exc:
        parser.error(f"invalid time value: {exc}")

    if since is not None and until is not None and since > until:
        parser.error("--since must not be after --until")

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

    entries = filter_entries(entries, since=since, until=until)
    report = build_report(entries, skipped=skipped, top=args.top)

    if args.json:
        print(render_json(report))
    else:
        print(render_table(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
