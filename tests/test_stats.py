"""Tests for report aggregation against the known sample fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

from logstats.parser import parse_lines
from logstats.stats import build_report, is_error_status

SAMPLE = Path(__file__).parent / "sample.log"


@pytest.fixture
def report():
    with SAMPLE.open(encoding="utf-8") as fh:
        entries, skipped = parse_lines(fh)
    return build_report(entries, skipped=skipped, top=3)


def test_totals_and_skipped(report) -> None:
    assert report.total_requests == 9
    assert report.skipped_lines == 1


def test_status_histogram(report) -> None:
    assert report.status_histogram == {200: 5, 301: 1, 404: 2, 500: 1}


def test_error_rate(report) -> None:
    # 4 errors (404, 404, 500 -> actually 3 errors) out of 9
    assert report.error_count == 3
    assert report.error_rate == pytest.approx(3 / 9 * 100)


def test_top_ips(report) -> None:
    top_ip, count = report.top_ips[0]
    assert top_ip == "192.168.0.1"
    assert count == 4
    assert len(report.top_ips) == 3


def test_top_urls(report) -> None:
    top_url, count = report.top_urls[0]
    assert top_url == "/index.html"
    assert count == 4


def test_peak_minute(report) -> None:
    minute, count = report.peak_minute
    assert minute == "2000-10-10T13:57"
    assert count == 3


def test_is_error_status() -> None:
    assert is_error_status(404)
    assert is_error_status(500)
    assert not is_error_status(200)
    assert not is_error_status(301)


def test_top_must_be_positive() -> None:
    with pytest.raises(ValueError):
        build_report([], top=0)


def test_empty_report() -> None:
    rep = build_report([], skipped=0, top=5)
    assert rep.total_requests == 0
    assert rep.error_rate == 0.0
    assert rep.peak_minute is None
