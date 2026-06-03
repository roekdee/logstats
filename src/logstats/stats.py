"""Aggregation of parsed log entries into analytics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .parser import LogEntry


@dataclass
class Report:
    """Aggregated analytics over a set of log entries."""

    total_requests: int = 0
    skipped_lines: int = 0
    status_histogram: dict[int, int] = field(default_factory=dict)
    top_ips: list[tuple[str, int]] = field(default_factory=list)
    top_urls: list[tuple[str, int]] = field(default_factory=list)
    requests_per_minute: list[tuple[str, int]] = field(default_factory=list)
    peak_minute: tuple[str, int] | None = None
    error_count: int = 0
    error_rate: float = 0.0

    def to_dict(self) -> dict:
        """Return a JSON-serialisable representation."""
        return {
            "total_requests": self.total_requests,
            "skipped_lines": self.skipped_lines,
            "status_histogram": {str(k): v for k, v in self.status_histogram.items()},
            "top_ips": [{"ip": ip, "count": c} for ip, c in self.top_ips],
            "top_urls": [{"url": u, "count": c} for u, c in self.top_urls],
            "requests_per_minute": [
                {"minute": m, "count": c} for m, c in self.requests_per_minute
            ],
            "peak_minute": (
                {"minute": self.peak_minute[0], "count": self.peak_minute[1]}
                if self.peak_minute
                else None
            ),
            "error_count": self.error_count,
            "error_rate": round(self.error_rate, 4),
        }


def is_error_status(status: int) -> bool:
    """Treat any 4xx or 5xx response as an error."""
    return status >= 400


def build_report(
    entries: list[LogEntry], skipped: int = 0, top: int = 5
) -> Report:
    """Aggregate ``entries`` into a :class:`Report`.

    ``top`` controls how many of the top IPs / URLs / busiest minutes to keep.
    """
    if top < 1:
        raise ValueError("top must be >= 1")

    total = len(entries)
    status_counter: Counter[int] = Counter()
    ip_counter: Counter[str] = Counter()
    url_counter: Counter[str] = Counter()
    minute_counter: Counter[str] = Counter()
    error_count = 0

    for entry in entries:
        status_counter[entry.status] += 1
        ip_counter[entry.ip] += 1
        url_counter[entry.url] += 1
        minute_counter[entry.minute_bucket] += 1
        if is_error_status(entry.status):
            error_count += 1

    error_rate = (error_count / total * 100.0) if total else 0.0
    peak = None
    if minute_counter:
        peak_minute, peak_count = max(
            minute_counter.items(), key=lambda kv: (kv[1], kv[0])
        )
        peak = (peak_minute, peak_count)

    return Report(
        total_requests=total,
        skipped_lines=skipped,
        status_histogram=dict(sorted(status_counter.items())),
        top_ips=ip_counter.most_common(top),
        top_urls=url_counter.most_common(top),
        requests_per_minute=minute_counter.most_common(top),
        peak_minute=peak,
        error_count=error_count,
        error_rate=error_rate,
    )
