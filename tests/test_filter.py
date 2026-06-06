"""Tests for --since/--until time filtering."""

from __future__ import annotations

from datetime import datetime

import pytest

from logstats.parser import (
    filter_entries,
    in_time_range,
    parse_line,
    parse_time_bound,
)


def _entry(hhmm: str):
    """Build a LogEntry at 2000-10-10 with the given HH:MM:SS (tz -0700)."""
    line = (
        f'1.2.3.4 - - [10/Oct/2000:{hhmm} -0700] '
        f'"GET /x HTTP/1.1" 200 1'
    )
    entry = parse_line(line)
    assert entry is not None
    return entry


def test_parse_time_bound_accepts_iso_date() -> None:
    assert parse_time_bound("2000-10-10") == datetime(2000, 10, 10, 0, 0, 0)


def test_parse_time_bound_accepts_iso_datetime() -> None:
    assert parse_time_bound("2000-10-10T13:57") == datetime(2000, 10, 10, 13, 57)


def test_parse_time_bound_accepts_space_separator() -> None:
    assert parse_time_bound("2000-10-10 13:57:30") == datetime(
        2000, 10, 10, 13, 57, 30
    )


def test_parse_time_bound_drops_timezone() -> None:
    assert parse_time_bound("2000-10-10T13:57+05:00").tzinfo is None


def test_parse_time_bound_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        parse_time_bound("not-a-time")


def test_since_boundary_is_inclusive() -> None:
    entry = _entry("13:57:00")
    assert in_time_range(entry, since=datetime(2000, 10, 10, 13, 57, 0))


def test_until_boundary_is_inclusive() -> None:
    entry = _entry("13:57:00")
    assert in_time_range(entry, until=datetime(2000, 10, 10, 13, 57, 0))


def test_just_before_since_is_excluded() -> None:
    entry = _entry("13:56:59")
    assert not in_time_range(entry, since=datetime(2000, 10, 10, 13, 57, 0))


def test_just_after_until_is_excluded() -> None:
    entry = _entry("13:57:01")
    assert not in_time_range(entry, until=datetime(2000, 10, 10, 13, 57, 0))


def test_filter_entries_keeps_range_inclusive() -> None:
    entries = [_entry("13:55:00"), _entry("13:56:00"), _entry("13:57:00")]
    kept = filter_entries(
        entries,
        since=datetime(2000, 10, 10, 13, 56, 0),
        until=datetime(2000, 10, 10, 13, 57, 0),
    )
    assert len(kept) == 2


def test_filter_entries_no_bounds_returns_input() -> None:
    entries = [_entry("13:55:00")]
    assert filter_entries(entries) is entries


def test_filter_compares_wall_clock_not_utc() -> None:
    # Timestamp is 13:57 local (-0700); a naive bound of 13:57 must match,
    # i.e. we compare wall-clock time, not the UTC instant (20:57).
    entry = _entry("13:57:00")
    assert in_time_range(
        entry,
        since=datetime(2000, 10, 10, 13, 57, 0),
        until=datetime(2000, 10, 10, 13, 57, 0),
    )
