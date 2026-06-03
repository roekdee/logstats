"""Parsing of Common/Combined Log Format access-log lines."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

# Common Log Format:
#   127.0.0.1 - frank [10/Oct/2000:13:55:36 -0700] "GET /a.gif HTTP/1.0" 200 2326
# Combined Log Format appends: "<referer>" "<user-agent>"
_LINE_RE = re.compile(
    r'^(?P<ip>\S+)'
    r'\s+\S+'  # identity (ignored)
    r'\s+\S+'  # auth user (ignored)
    r'\s+\[(?P<time>[^\]]+)\]'
    r'\s+"(?P<method>\S+)\s+(?P<url>\S+)\s+(?P<proto>[^"]*)"'
    r'\s+(?P<status>\d{3})'
    r'\s+(?P<size>\d+|-)'
    r'(?:\s+"(?P<referer>[^"]*)"\s+"(?P<agent>[^"]*)")?'
    r'\s*$'
)

_TIME_FMT = "%d/%b/%Y:%H:%M:%S %z"


@dataclass(frozen=True)
class LogEntry:
    """A single parsed access-log line."""

    ip: str
    timestamp: datetime
    method: str
    url: str
    status: int
    size: int

    @property
    def minute_bucket(self) -> str:
        """Timestamp truncated to the minute, as an ISO-like string."""
        return self.timestamp.strftime("%Y-%m-%dT%H:%M")


def parse_line(line: str) -> LogEntry | None:
    """Parse a single log line.

    Returns a :class:`LogEntry` on success, or ``None`` for blank or
    malformed lines (which the caller is expected to skip and count).
    """
    line = line.rstrip("\n")
    if not line.strip():
        return None

    match = _LINE_RE.match(line)
    if match is None:
        return None

    try:
        timestamp = datetime.strptime(match["time"], _TIME_FMT)
    except ValueError:
        return None

    raw_size = match["size"]
    size = 0 if raw_size == "-" else int(raw_size)

    return LogEntry(
        ip=match["ip"],
        timestamp=timestamp,
        method=match["method"],
        url=match["url"],
        status=int(match["status"]),
        size=size,
    )


def parse_lines(lines: object) -> tuple[list[LogEntry], int]:
    """Parse an iterable of lines.

    Returns a tuple of ``(entries, skipped)`` where ``skipped`` is the number
    of non-blank lines that failed to parse.
    """
    entries: list[LogEntry] = []
    skipped = 0
    for line in lines:  # type: ignore[union-attr]
        if not line.strip():
            continue
        entry = parse_line(line)
        if entry is None:
            skipped += 1
        else:
            entries.append(entry)
    return entries, skipped
