# eval-run-ledger

[![CI](https://github.com/Trysac/u131-eval-run-ledger/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u131-eval-run-ledger/actions)

Append-only JSONL ledger of evaluation runs, using an injected clock for timing and strict Decimal accounting for costs.

## Problem

Teams compare evaluation runs on quality but often lack structured visibility into duration and cost per evaluation run. Per-call LLM cost trackers exist, but nothing records the evaluation run as a single atomic unit. This library provides a constant-memory, append-only, and diffable ledger.

## Installation

```bash
pip install eval-run-ledger
```

## Usage

```python
from datetime import datetime, timezone
from eval_run_ledger import start_run, append_record

run = start_run("eval-01", clock=lambda: datetime.now(timezone.utc))
run.add_case("0.05", tokens_in=500, tokens_out=120)
record = run.finish()
append_record("eval_ledger.jsonl", record)
```

## Public API Summary

- `start_run(run_id: str, *, clock: Callable[[], datetime]) -> Run`: Initializes a tracker. Rejects invalid run_id (must match `^[A-Za-z0-9._-]+$`).
- `Run.add_case(cost_usd: str | Decimal, *, tokens_in: int = 0, tokens_out: int = 0) -> None`: Accumulates metrics. Rejects floats to prevent precision loss.
- `Run.finish() -> RunRecord`: Finalizes the run. Detects clock skew (time moving backward) and naive datetimes.
- `RunRecord`: Frozen dataclass for storing results.
- `append_record(path, record)`: Saves a record to JSONL. Automatically creates parent directories.
- `read_records(path, *, max_bytes=10_000_000)`: Parses the ledger. Fails on files larger than `max_bytes`.
- `LedgerError`: Raised for operational errors, providing error codes (`already_finished`, `corrupt_line`, etc.).

## Why not alternative?

The evaluation run is the atomic unit of comparison. Unlike per-call LLM pricing tables, `eval-run-ledger` records the run as a compact, exact, and diffable JSON line, ensuring minimal disk usage and simple analysis.

## Security

See [docs/SECURITY.md](docs/SECURITY.md).