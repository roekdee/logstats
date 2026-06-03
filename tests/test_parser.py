"""Tests for the log line parser."""

from __future__ import annotations

from logstats.parser import parse_line, parse_lines

COMMON = '127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /a.gif HTTP/1.0" 200 2326'
COMBINED = (
    '10.0.0.5 - - [10/Oct/2000:13:56:01 -0700] "POST /login HTTP/1.1" 200 87 '
    '"http://example.com/" "Mozilla/5.0"'
)


def test_parses_common_log_format() -> None:
    entry = parse_line(COMMON)
    assert entry is not None
    assert entry.ip == "127.0.0.1"
    assert entry.method == "GET"
    assert entry.url == "/a.gif"
    assert entry.status == 200
    assert entry.size == 2326
    assert entry.minute_bucket == "2000-10-10T13:55"


def test_parses_combined_log_format() -> None:
    entry = parse_line(COMBINED)
    assert entry is not None
    assert entry.ip == "10.0.0.5"
    assert entry.method == "POST"
    assert entry.url == "/login"
    assert entry.status == 200


def test_dash_size_becomes_zero() -> None:
    line = '1.2.3.4 - - [10/Oct/2000:13:58:00 -0700] "GET /x HTTP/1.1" 301 -'
    entry = parse_line(line)
    assert entry is not None
    assert entry.size == 0


def test_malformed_line_returns_none() -> None:
    assert parse_line("this is not a log line") is None


def test_blank_line_returns_none() -> None:
    assert parse_line("   ") is None


def test_bad_timestamp_returns_none() -> None:
    line = '1.2.3.4 - - [99/XXX/0000:99:99:99 +0000] "GET /x HTTP/1.1" 200 1'
    assert parse_line(line) is None


def test_parse_lines_counts_skipped() -> None:
    lines = [COMMON, "garbage line", COMBINED, "", "   "]
    entries, skipped = parse_lines(lines)
    assert len(entries) == 2
    assert skipped == 1  # blank lines are not counted as skipped
