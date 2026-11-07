# Testing

## Running

Use `pytest` to run the suite, which asserts observable effects like return values and specific `LedgerError` codes.

## Existing Tests

The test suite is located in `tests/test_eval_run_ledger.py`. It specifically covers:
- Acceptance criteria: Verifying calculation of cost (Decimal quantization) and duration (total_seconds).
- Error paths: Verifying that invalid types (e.g., float costs, boolean tokens) raise `LedgerError`.
- State handling: Verifying that finishing an already finished run, or using naive/backward-skewed clocks, raises the correct error.
- File I/O: Verifying record appending and reading, including file-size limits (`input_too_large`) and JSON parsing errors (`corrupt_line`).