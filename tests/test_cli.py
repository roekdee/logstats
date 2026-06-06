"""Tests for the CLI, both in-process and via subprocess."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from logstats.cli import main

SAMPLE = Path(__file__).parent / "sample.log"


def test_main_table_output(capsys) -> None:
    code = main([str(SAMPLE)])
    assert code == 0
    out = capsys.readouterr().out
    assert "logstats report" in out
    assert "Total requests : 9" in out
    assert "192.168.0.1" in out


def test_main_json_output(capsys) -> None:
    code = main([str(SAMPLE), "--json", "--top", "2"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_requests"] == 9
    assert payload["skipped_lines"] == 1
    assert len(payload["top_ips"]) == 2
    assert payload["top_ips"][0] == {"ip": "192.168.0.1", "count": 4}
    assert payload["status_histogram"]["200"] == 5


def test_main_missing_file_returns_2(capsys) -> None:
    code = main(["does-not-exist.log"])
    assert code == 2
    assert "cannot open" in capsys.readouterr().err


def test_main_since_filters_early_lines(capsys) -> None:
    # Sample log spans 13:55..13:58. Keep only 13:57 onward (4 lines).
    code = main([str(SAMPLE), "--json", "--since", "2000-10-10T13:57"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_requests"] == 4
    # Skipped count is unaffected by filtering.
    assert payload["skipped_lines"] == 1


def test_main_until_filters_late_lines(capsys) -> None:
    # Keep only lines up to and including 13:55 (2 lines).
    code = main([str(SAMPLE), "--json", "--until", "2000-10-10T13:55:59"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_requests"] == 2


def test_main_since_until_combined_with_stats(capsys) -> None:
    # Window 13:56:00..13:57:30 inclusive -> 6 lines (13:56:01, 13:56:05,
    # 13:56:10, 13:57:22, 13:57:25, 13:57:30), including all three errors
    # at 13:56:05 (404), 13:57:22 (500) and 13:57:25 (404).
    code = main(
        [
            str(SAMPLE),
            "--json",
            "--since",
            "2000-10-10T13:56:00",
            "--until",
            "2000-10-10T13:57:30",
        ]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_requests"] == 6
    assert payload["error_count"] == 3


def test_main_until_boundary_is_inclusive(capsys) -> None:
    # A line exists exactly at 13:55:40; an --until at that second keeps it.
    code = main([str(SAMPLE), "--json", "--until", "2000-10-10T13:55:40"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_requests"] == 2


def test_main_date_only_since_keeps_whole_day(capsys) -> None:
    # A bare date keeps the whole day.
    code = main([str(SAMPLE), "--json", "--since", "2000-10-10"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total_requests"] == 9


def test_main_rejects_bad_time(capsys) -> None:
    try:
        main([str(SAMPLE), "--since", "yesterday"])
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover
        raise AssertionError("expected SystemExit")
    assert "invalid time value" in capsys.readouterr().err


def test_main_rejects_inverted_range(capsys) -> None:
    try:
        main(
            [
                str(SAMPLE),
                "--since",
                "2000-10-10T13:58",
                "--until",
                "2000-10-10T13:55",
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover
        raise AssertionError("expected SystemExit")
    assert "--since must not be after --until" in capsys.readouterr().err


def test_main_rejects_bad_top(capsys) -> None:
    try:
        main([str(SAMPLE), "--top", "0"])
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover
        raise AssertionError("expected SystemExit")


def test_cli_via_subprocess_stdin() -> None:
    log = SAMPLE.read_text(encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "logstats.cli", "--json"],
        input=log,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["total_requests"] == 9
    assert payload["error_count"] == 3
