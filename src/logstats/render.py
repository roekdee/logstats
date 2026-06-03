"""Rendering of a :class:`Report` to JSON or a human-readable table."""

from __future__ import annotations

import json

from .stats import Report


def render_json(report: Report) -> str:
    """Render the report as pretty-printed JSON."""
    return json.dumps(report.to_dict(), indent=2)


def _section(title: str) -> str:
    return f"\n{title}\n{'-' * len(title)}"


def _rows(pairs: list[tuple[str, int]], label: str) -> list[str]:
    if not pairs:
        return ["  (none)"]
    width = max(len(str(k)) for k, _ in pairs)
    width = max(width, len(label))
    lines = [f"  {label:<{width}}  count"]
    for key, count in pairs:
        lines.append(f"  {str(key):<{width}}  {count}")
    return lines


def render_table(report: Report) -> str:
    """Render the report as a plain-text table."""
    lines: list[str] = []
    lines.append("logstats report")
    lines.append("===============")
    lines.append(f"Total requests : {report.total_requests}")
    lines.append(f"Skipped lines  : {report.skipped_lines}")
    lines.append(
        f"Error rate     : {report.error_rate:.2f}% "
        f"({report.error_count} errors)"
    )
    if report.peak_minute:
        minute, count = report.peak_minute
        lines.append(f"Peak minute    : {minute} ({count} requests)")

    lines.append(_section("Status codes"))
    if report.status_histogram:
        for status, count in report.status_histogram.items():
            lines.append(f"  {status}  {count}")
    else:
        lines.append("  (none)")

    lines.append(_section(f"Top {len(report.top_ips)} IPs"))
    lines.extend(_rows(report.top_ips, "ip"))

    lines.append(_section(f"Top {len(report.top_urls)} URLs"))
    lines.extend(_rows(report.top_urls, "url"))

    lines.append(_section("Busiest minutes"))
    lines.extend(_rows(report.requests_per_minute, "minute"))

    return "\n".join(lines)
