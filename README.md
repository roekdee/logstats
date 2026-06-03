# logstats

![CI](https://github.com/roekdee/logstats/actions/workflows/ci.yml/badge.svg)

A little CLI I wrote to get a quick read on web-server access logs without opening up a spreadsheet or grepping by hand. Point it at a log file (Common or Combined Log Format) and it prints the total requests, a status-code histogram, the error rate, the busiest minute, and the top IPs and URLs. It's all standard library, no dependencies.

## Install

```bash
pip install -e .
```

Needs Python 3.12+.

## Usage

```bash
logstats access.log              # from a file
cat access.log | logstats        # or from stdin
logstats access.log --top 10 --json
```

`--top N` controls how many IPs/URLs/minutes you see (default 5). `--json` swaps the table for JSON if you want to pipe it somewhere. Malformed lines get skipped and counted rather than blowing up.

There's a sample log in `tests/sample.log` to try it against:

```bash
logstats tests/sample.log
```

Table output looks like this:

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
  404  2
```

## Run tests

```bash
pip install -e ".[dev]"
ruff check .
pytest -q
```

## Notes

I kept it to the standard library on purpose — `argparse` + `re` + `collections` cover everything here, and it means there's nothing to install before it runs. The parsing is just a regex for the two common log formats; if your logs use a custom format it won't match and those lines get counted as skipped.

It reads the whole file into memory rather than streaming, which is fine for the log sizes I deal with but would need rework for multi-GB files. If I come back to it, true streaming and maybe a `--since`/`--until` time filter are the first things I'd add.

## License

[MIT](LICENSE) © 2026 Roekdee
