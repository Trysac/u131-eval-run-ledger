"""CLI entry point for eval_run_ledger."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from decimal import Decimal

from eval_run_ledger.ledger import read_records


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eval-run-ledger", description="Evaluation run ledger CLI"
    )
    subparsers = parser.add_subparsers(dest="command")
    summary_parser = subparsers.add_parser("summary", help="Print summary metrics across runs")
    summary_parser.add_argument("path", help="Path to ledger JSONL file")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI main function. Returns 0 on success, 2 on usage or IO errors."""
    if argv is None:
        argv = sys.argv[1:]

    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits with code 2 on syntax error
        return 2 if exc.code != 0 else 0

    if args.command != "summary":
        sys.stderr.write("Error: unknown or missing command\n")
        return 2

    try:
        records = read_records(args.path)
    except Exception as exc:
        sys.stderr.write(f"Error reading ledger: {exc}\n")
        return 2

    runs_count = len(records)
    if runs_count == 0:
        print("runs: 0, cases: 0, cost_usd: 0, duration_s: 0.0")
        return 0

    total_cases = sum(r.cases for r in records)
    total_cost: Decimal = sum((r.cost_usd for r in records), Decimal("0"))
    total_duration: float = sum(r.duration_s for r in records)

    print(
        f"runs: {runs_count}, cases: {total_cases}, "
        f"cost_usd: {total_cost}, duration_s: {total_duration!r}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
