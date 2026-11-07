"""Tests for eval_run_ledger covering acceptance criteria and error paths."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from eval_run_ledger import (
    LedgerError,
    append_record,
    read_records,
    start_run,
)
from eval_run_ledger.__main__ import main


def test_acceptance_criteria_1() -> None:
    times = [
        datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 0, 1, 30, tzinfo=timezone.utc),
    ]
    it = iter(times)

    def clock() -> datetime:
        return next(it)

    run = start_run("r1", clock=clock)
    run.add_case("0.10")
    run.add_case("0.10")
    run.add_case("0.10")
    rec = run.finish()

    assert rec.duration_s == 90.0
    assert rec.cases == 3
    assert rec.cost_usd == Decimal("0.30")
    assert rec.cost_per_case == Decimal("0.100000")
    assert rec.tokens_in == 0
    assert rec.tokens_out == 0


def test_acceptance_criteria_2() -> None:
    now = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    run = start_run("r-test", clock=lambda: now)

    with pytest.raises(LedgerError) as exc_info:
        run.add_case(0.1)
    assert exc_info.value.code == "invalid_cost"

    with pytest.raises(LedgerError) as exc_info:
        run.add_case("-0.01")
    assert exc_info.value.code == "invalid_cost"

    with pytest.raises(LedgerError) as exc_info:
        run.add_case("NaN")
    assert exc_info.value.code == "invalid_cost"

    with pytest.raises(LedgerError) as exc_info:
        run.add_case("0.05", tokens_in=-1)
    assert exc_info.value.code == "invalid_tokens"

    with pytest.raises(LedgerError) as exc_info:
        run.add_case("0.05", tokens_out=-5)
    assert exc_info.value.code == "invalid_tokens"

    with pytest.raises(LedgerError) as exc_info:
        run.add_case("0.05", tokens_in=True)  # type: ignore[arg-type]
    assert exc_info.value.code == "invalid_tokens"


def test_acceptance_criteria_3() -> None:
    t1 = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 1, 1, 10, 5, tzinfo=timezone.utc)
    clock_vals = [t1, t2]
    it = iter(clock_vals)

    run = start_run("r-finished", clock=lambda: next(it))
    run.finish()

    with pytest.raises(LedgerError) as exc_info:
        run.add_case("0.01")
    assert exc_info.value.code == "already_finished"

    with pytest.raises(LedgerError) as exc_info:
        run.finish()
    assert exc_info.value.code == "already_finished"

    # Naive datetime
    def naive_clock():
        return datetime(2026, 1, 1, 0, 0)

    with pytest.raises(LedgerError) as exc_info:
        start_run("r-naive", clock=naive_clock)
    assert exc_info.value.code == "naive_datetime"

    # Clock backwards
    backwards_clock_vals = [
        datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 9, 59, tzinfo=timezone.utc),
    ]
    b_it = iter(backwards_clock_vals)
    run_backwards = start_run("r-backwards", clock=lambda: next(b_it))
    with pytest.raises(LedgerError) as exc_info:
        run_backwards.finish()
    assert exc_info.value.code == "clock_went_backwards"


def test_acceptance_criteria_4(tmp_path: Path) -> None:
    times = [
        datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 0, 1, 30, tzinfo=timezone.utc),
    ]
    it = iter(times)
    run = start_run("r1", clock=lambda: next(it))
    run.add_case("0.10")
    run.add_case("0.10")
    run.add_case("0.10")
    record = run.finish()

    ledger_file = tmp_path / "eval_runs.jsonl"
    append_record(ledger_file, record)

    content = ledger_file.read_text(encoding="utf-8")
    expected = (
        '{"cases":3,"cost_per_case":"0.100000","cost_usd":"0.30","duration_s":90.0,'
        '"finished_at":"2026-01-01T00:01:30+00:00","run_id":"r1",'
        '"started_at":"2026-01-01T00:00:00+00:00","tokens_in":0,"tokens_out":0}\n'
    )
    assert content == expected

    read_back = read_records(ledger_file)
    assert read_back == [record]


def test_acceptance_criteria_5(tmp_path: Path) -> None:
    corrupt_file = tmp_path / "corrupt.jsonl"
    # Create a valid first line, then a corrupt second line
    valid_record = (
        '{"cases":1,"cost_per_case":"0.100000","cost_usd":"0.10","duration_s":1.0,'
        '"finished_at":"2026-01-01T00:01:00+00:00","run_id":"r1",'
        '"started_at":"2026-01-01T00:00:00+00:00","tokens_in":0,"tokens_out":0}'
    )
    corrupt_file.write_text(f"{valid_record}\nnot json\n", encoding="utf-8")

    with pytest.raises(LedgerError) as exc_info:
        read_records(corrupt_file)
    assert exc_info.value.code == "corrupt_line"
    assert exc_info.value.line == 2

    # Test max_bytes limit
    large_file = tmp_path / "large.jsonl"
    # Create a dummy file with 10_000_001 bytes
    with open(large_file, "wb") as f:
        f.seek(10_000_001 - 1)
        f.write(b"0")

    with pytest.raises(LedgerError) as exc_info:
        read_records(large_file, max_bytes=10_000_000)
    assert exc_info.value.code == "input_too_large"


def test_acceptance_criteria_6(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "two_runs.jsonl"

    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(seconds=90.0)
    t2 = datetime(2026, 1, 1, 2, 0, tzinfo=timezone.utc)
    t3 = t2 + timedelta(seconds=30.0)

    clock1 = iter([t0, t1])
    run1 = start_run("run-1", clock=lambda: next(clock1))
    run1.add_case("0.10")
    run1.add_case("0.10")
    run1.add_case("0.10")
    r1 = run1.finish()
    append_record(path, r1)

    clock2 = iter([t2, t3])
    run2 = start_run("run-2", clock=lambda: next(clock2))
    run2.add_case("0.10")
    run2.add_case("0.10")
    r2 = run2.finish()
    append_record(path, r2)

    rc = main(["summary", str(path)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.strip() == "runs: 2, cases: 5, cost_usd: 0.50, duration_s: 120.0"

    missing_path = tmp_path / "does_not_exist.jsonl"
    rc_missing = main(["summary", str(missing_path)])
    assert rc_missing == 2


def test_zero_cases_and_empty_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    t0 = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 1, 1, 0, 0, 10, tzinfo=timezone.utc)
    it = iter([t0, t1])
    run = start_run("empty-run", clock=lambda: next(it))
    record = run.finish()
    assert record.cases == 0
    assert record.cost_per_case == Decimal("0.000000")
    assert record.cost_usd == Decimal("0")
    assert record.duration_s == 10.0

    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("\n\n", encoding="utf-8")
    assert read_records(empty_file) == []

    rc = main(["summary", str(empty_file)])
    captured = capsys.readouterr()
    assert rc == 0
    assert captured.out.strip() == "runs: 0, cases: 0, cost_usd: 0, duration_s: 0.0"


def test_run_id_validation() -> None:
    def valid_clock():
        return datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc)

    start_run("valid_id-1.0", clock=valid_clock)

    # Empty run_id
    with pytest.raises(LedgerError) as exc:
        start_run("", clock=valid_clock)
    assert exc.value.code == "invalid_run_id"

    # Long run_id > 128 chars
    with pytest.raises(LedgerError) as exc:
        start_run("a" * 129, clock=valid_clock)
    assert exc.value.code == "invalid_run_id"

    # Unicode / invalid chars
    for bad in ["run id", "run/1", "run:1", "run_⚡", "run@1", "rühn"]:
        with pytest.raises(LedgerError) as exc:
            start_run(bad, clock=valid_clock)
        assert exc.value.code == "invalid_run_id"


def test_corrupt_records(tmp_path: Path) -> None:
    file = tmp_path / "corrupt_fields.jsonl"
    # Missing keys
    file.write_text('{"cases": 1}\n', encoding="utf-8")
    with pytest.raises(LedgerError) as exc:
        read_records(file)
    assert exc.value.code == "corrupt_line"
    assert exc.value.line == 1

    # Invalid value inside JSON
    file.write_text(
        '{"cases":-1,"cost_per_case":"0.1","cost_usd":"0.1","duration_s":1.0,"finished_at":"2026-01-01T00:01:00+00:00","run_id":"r1","started_at":"2026-01-01T00:00:00+00:00","tokens_in":0,"tokens_out":0}\n',
        encoding="utf-8",
    )
    with pytest.raises(LedgerError) as exc:
        read_records(file)
    assert exc.value.code == "corrupt_line"


def test_cli_errors(capsys: pytest.CaptureFixture[str]) -> None:
    # No command
    assert main([]) == 2
    # Bad command
    assert main(["unknown"]) == 2
    # Extra argument handling
    assert main(["summary"]) == 2


def test_add_case_with_cost_0_20() -> None:
    times = [
        datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
    ]
    it = iter(times)
    run = start_run("test-020", clock=lambda: next(it))
    run.add_case("0.20")
    record = run.finish()
    assert record.cost_usd == Decimal("0.20")
