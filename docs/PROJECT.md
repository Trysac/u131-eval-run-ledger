# Project record

## Objective

To provide an append-only JSONL ledger of evaluation runs, capturing duration via injected clock, case counts, tokens, and Decimal costs, while providing a summary CLI.

## Scope

The library manages run state, validation (via types and regex), and JSONL I/O. It enforces UTC timezones and uses `Decimal` for financial precision.

## Out of Scope

- Budgets and automated alerting.
- Per-call LLM pricing lookup tables.
- Concurrency controls (file locking).
- Dashboards and UI visualization.

## Effort metrics

| Metric | Value |
|---|---|
| Tokens (input / output) | 468897 / 30504 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.1431 |

## Factory run u131 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | gemini-3.8-flash | yes | 4181 | 724 | 0 | 0 | 0.0029 |
| generation | gemini-3.8-flash | yes | 4181 | 8874 | 0 | 0 | 0.0182 |
| generation | gemini-3.8-flash | yes | 4215 | 8647 | 0 | 0 | 0.0178 |
| generation | gemini-3.8-flash | yes | 4215 | 8423 | 0 | 0 | 0.0174 |
| fix-1 | gemini-3.1-flash-lite | no | 29756 | 978 | 0 | 36440 | 0.0098 |
| fix-2 | gemini-3.1-flash-lite | no | 29116 | 563 | 0 | 20323 | 0.0086 |
| fix-3 | gemini-3.1-flash-lite | no | 23122 | 785 | 0 | 22268 | 0.0075 |
| audit | gemini-3.1-flash-lite | no | 36711 | 230 | 0 | 62915 | 0.0111 |
| docs | gemini-3.1-flash-lite | no | 191454 | 1280 | 0 | 0 | 0.0498 |

Total: $0.1431. Prices: Anthropic list prices.
