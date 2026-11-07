# eval-run-ledger

[![PyPI version](https://img.shields.io/pypi/v/trysac-eval-run-ledger)](https://pypi.org/project/trysac-eval-run-ledger/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-eval-run-ledger)](LICENSE)
[![CI](https://github.com/Trysac/u131-eval-run-ledger/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u131-eval-run-ledger/actions/workflows/ci.yml)

Append-only JSONL ledger of evaluation runs: duration from an injected clock, case count, tokens and Decimal cost per run, with a summary CLI

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-eval-run-ledger
# or
uv add trysac-eval-run-ledger
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import eval_run_ledger

# normalize() trims surrounding whitespace and lower-cases the text.
print(eval_run_ledger.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    eval_run_ledger.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
