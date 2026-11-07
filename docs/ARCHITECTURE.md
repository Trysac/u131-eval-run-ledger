# Architecture

`eval-run-ledger` implements a lightweight, append-only ledger for AI evaluation runs.

## Design Principles

1. **Deterministic & Injectable Clocks**: Wall-clock time is injected via a `Callable[[], datetime]`, enforcing timezone-aware UTC timestamps and detecting clock backward skews.
2. **Exact Decimal Accounting**: Floats are rejected to prevent floating-point inaccuracy. Costs are stored and computed using Python standard library `Decimal` with rounding half-even for cost-per-case.
3. **Constant Memory Footprint**: The `Run` object does not buffer individual case events; it tracks aggregate totals in memory.
4. **Canonical JSONL Serialisation**: Run summaries are written as compact, sorted-key JSON lines terminated by `\n`.
