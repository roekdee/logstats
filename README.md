# logstats

Turn web-server access logs into instant analytics — status histogram, top IPs/URLs, error rate, and traffic peaks — with zero dependencies.

![CI](https://github.com/roekdee/logstats/actions/workflows/ci.yml/badge.svg)

## Features

- Parses **Common** and **Combined** Log Format access logs
- Total requests, **status-code histogram**, and **% error rate** (4xx/5xx)
- **Top N** client IPs and requested URLs
- **Requests-per-minute** buckets with the busiest (peak) minute
- Reads from a **file** or **stdin** (pipe-friendly)
- **Table** or **JSON** output (`--json`) and configurable `--top N`
- Skips malformed lines gracefully and reports how many were skipped
- Pure Python standard library — `argparse`, `re`, `collections`

## Install

```bash
pip install -e .
```

Requires Python 3.12+.

## Usage

```bash
# From a file
logstats access.log

# From stdin
cat access.log | logstats

# Show the top 10 and emit JSON
logstats access.log --top 10 --json
```

### Sample output (table)

```text
logstats report
===============
Total requests : 9
Skipped lines  : 1
Error rate     : 33.33% (3 errors)
Peak minute    : 2000-10-10T13:57 (3 requests)

Status codes
------------
  200  5
  301  1
  404  2
  500  1

Top 3 IPs
---------
  ip           count
  192.168.0.1  4
  10.0.0.5     3
  172.16.0.9   2
```

### Sample output (`--json`)

```json
{
  "total_requests": 9,
  "skipped_lines": 1,
  "status_histogram": { "200": 5, "301": 1, "404": 2, "500": 1 },
  "top_ips": [{ "ip": "192.168.0.1", "count": 4 }],
  "error_count": 3,
  "error_rate": 33.3333
}
```

A small fixture lives at [`tests/sample.log`](tests/sample.log) if you want something to run against immediately:

```bash
logstats tests/sample.log
```

## Run tests

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
```

## Tech

- Python 3.12+ standard library only (`argparse`, `re`, `collections`, `dataclasses`)
- `src/` layout with a `console_scripts` entry point
- `pytest` for unit + CLI (subprocess) tests
- `ruff` for linting
- GitHub Actions CI on push and pull request

## License

[MIT](LICENSE) © 2026 Roekdee
