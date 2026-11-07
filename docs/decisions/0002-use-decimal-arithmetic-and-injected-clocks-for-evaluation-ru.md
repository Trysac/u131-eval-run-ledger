# Use Decimal arithmetic and injected clocks for evaluation run accounting

Status: accepted (generated, pending human review)

## Context

Floating point arithmetic causes cumulative rounding errors across thousands of evaluation cases, and relying on system time directly impairs test determinism and ledger consistency.

## Decision

Use Python Decimal for all cost tracking and reject float inputs. Require a clock callable returning timezone-aware datetime instances, storing all timestamps in UTC.

## Consequences

Costs are exact and diffable across test environments. Run memory remains O(1) by maintaining running sums rather than case lists.
