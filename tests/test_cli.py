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
