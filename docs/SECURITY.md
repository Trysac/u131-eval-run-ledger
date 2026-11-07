# Security Policy

## Threat Model

`eval-run-ledger` processes local JSONL files and tracks run state in memory.

- **Defended**:
  - Denial of Service: `read_records` limits file size to 10MB to prevent unbounded memory usage.
  - Information Disclosure: `LedgerError` truncates diagnostic messages to under 200 characters to prevent log pollution.
  - Injection: Use of standard library `json` and `Decimal` ensures canonical parsing without code execution risks.

- **Not Defended**:
  - File tampering: The file format is plain text and does not support cryptographic integrity checks.
  - Concurrency: This utility does not implement cross-process file locking for the append-only ledger.