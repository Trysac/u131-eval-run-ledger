"""Core Run management and JSONL ledger serialisation."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from eval_run_ledger.errors import LedgerError

_RUN_ID_REGEX = re.compile(r"^[A-Za-z0-9._-]+$")
_COST_PER_CASE_EXPONENT = Decimal("0.000001")
_ZERO_COST_PER_CASE = Decimal("0.000000")


@dataclass(frozen=True)
class RunRecord:
    """Immutable summary of a completed evaluation run."""

    run_id: str
    started_at: datetime
    finished_at: datetime
    duration_s: float
    cases: int
    cost_usd: Decimal
    cost_per_case: Decimal
    tokens_in: int
    tokens_out: int

    def to_dict(self) -> dict[str, Any]:
        """Convert record to JSON-serialisable dictionary."""
        return {
            "cases": self.cases,
            "cost_per_case": str(self.cost_per_case),
            "cost_usd": str(self.cost_usd),
            "duration_s": self.duration_s,
            "finished_at": self.finished_at.isoformat(),
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
        }

    def to_json_line(self) -> str:
        """Serialize to a single sorted JSON string without trailing newline."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))


class Run:
    """Accumulates metrics for a single evaluation run with bounded constant memory."""

    def __init__(self, run_id: str, started_at: datetime) -> None:
        self._run_id = run_id
        self._started_at = started_at
        self._cases = 0
        self._cost_usd = Decimal("0")
        self._tokens_in = 0
        self._tokens_out = 0
        self._finished = False
        self._clock: Callable[[], datetime] | None = None

    def add_case(
        self,
        cost_usd: str | Decimal,
        *,
        tokens_in: int = 0,
        tokens_out: int = 0,
    ) -> None:
        """Add execution metrics for a single evaluation case."""
        if self._finished:
            raise LedgerError("already_finished", "Run has already finished")

        if isinstance(cost_usd, float):
            raise LedgerError("invalid_cost", "Cost cannot be a float; use str or Decimal")

        try:
            dec_cost = Decimal(cost_usd) if isinstance(cost_usd, str) else cost_usd
        except (InvalidOperation, TypeError, ValueError):
            raise LedgerError("invalid_cost", f"Invalid cost: {cost_usd!r}") from None

        if not isinstance(dec_cost, Decimal) or not dec_cost.is_finite() or dec_cost < 0:
            raise LedgerError("invalid_cost", f"Cost must be finite and >= 0, got {cost_usd!r}")

        if isinstance(tokens_in, bool) or not isinstance(tokens_in, int) or tokens_in < 0:
            raise LedgerError(
                "invalid_tokens", f"tokens_in must be a non-bool int >= 0, got {tokens_in!r}"
            )

        if isinstance(tokens_out, bool) or not isinstance(tokens_out, int) or tokens_out < 0:
            raise LedgerError(
                "invalid_tokens", f"tokens_out must be a non-bool int >= 0, got {tokens_out!r}"
            )

        self._cases += 1
        self._cost_usd += dec_cost
        self._tokens_in += tokens_in
        self._tokens_out += tokens_out

    def finish(self) -> RunRecord:
        """Finalize the run and return an immutable RunRecord."""
        if self._finished:
            raise LedgerError("already_finished", "Run has already finished")
        if self._clock is None:
            raise LedgerError("clock_went_backwards", "Clock is missing")

        raw_finish = self._clock()
        finished_at = _validate_datetime(raw_finish)

        if finished_at < self._started_at:
            raise LedgerError(
                "clock_went_backwards",
                f"Finish time {finished_at} precedes start time {self._started_at}",
            )

        self._finished = True
        duration_s = (finished_at - self._started_at).total_seconds()

        if self._cases == 0:
            cost_per_case = _ZERO_COST_PER_CASE
        else:
            cost_per_case = (self._cost_usd / Decimal(self._cases)).quantize(
                _COST_PER_CASE_EXPONENT, rounding=ROUND_HALF_EVEN
            )

        return RunRecord(
            run_id=self._run_id,
            started_at=self._started_at,
            finished_at=finished_at,
            duration_s=duration_s,
            cases=self._cases,
            cost_usd=self._cost_usd,
            cost_per_case=cost_per_case,
            tokens_in=self._tokens_in,
            tokens_out=self._tokens_out,
        )


def _validate_datetime(dt: datetime) -> datetime:
    if not isinstance(dt, datetime) or dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise LedgerError("naive_datetime", "Clock returned a naive datetime; timezone is required")
    return dt.astimezone(timezone.utc)


def start_run(run_id: str, *, clock: Callable[[], datetime]) -> Run:
    """Start a new evaluation run tracker."""
    if (
        not isinstance(run_id, str)
        or not (1 <= len(run_id) <= 128)
        or not _RUN_ID_REGEX.match(run_id)
    ):
        raise LedgerError("invalid_run_id", f"Invalid run_id: {run_id!r}")

    raw_start = clock()
    started_at = _validate_datetime(raw_start)

    run = Run(run_id=run_id, started_at=started_at)
    run._clock = clock
    return run


def append_record(path: str | Path, record: RunRecord) -> None:
    """Append a RunRecord as a single line to the specified JSONL path."""
    line = record.to_json_line() + "\n"
    p = Path(path)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, mode="a", encoding="utf-8", newline="\n") as f:
        f.write(line)


def _parse_record_dict(d: dict[str, Any], line_num: int) -> RunRecord:
    required_keys = {
        "cases",
        "cost_per_case",
        "cost_usd",
        "duration_s",
        "finished_at",
        "run_id",
        "started_at",
        "tokens_in",
        "tokens_out",
    }
    if not isinstance(d, dict) or set(d.keys()) != required_keys:
        raise LedgerError("corrupt_line", "Invalid record fields", line=line_num)

    try:
        run_id = d["run_id"]
        if not isinstance(run_id, str) or not _RUN_ID_REGEX.match(run_id):
            raise ValueError("invalid run_id")
        started_at = _validate_datetime(datetime.fromisoformat(d["started_at"]))
        finished_at = _validate_datetime(datetime.fromisoformat(d["finished_at"]))
        duration_s = float(d["duration_s"])
        cases = int(d["cases"])
        if isinstance(d["cases"], bool) or cases < 0:
            raise ValueError("invalid cases")
        tokens_in = int(d["tokens_in"])
        if isinstance(d["tokens_in"], bool) or tokens_in < 0:
            raise ValueError("invalid tokens_in")
        tokens_out = int(d["tokens_out"])
        if isinstance(d["tokens_out"], bool) or tokens_out < 0:
            raise ValueError("invalid tokens_out")
        cost_usd = Decimal(str(d["cost_usd"]))
        cost_per_case = Decimal(str(d["cost_per_case"]))
    except Exception as exc:
        raise LedgerError(
            "corrupt_line", f"Corrupt record structure: {exc}", line=line_num
        ) from exc

    return RunRecord(
        run_id=run_id,
        started_at=started_at,
        finished_at=finished_at,
        duration_s=duration_s,
        cases=cases,
        cost_usd=cost_usd,
        cost_per_case=cost_per_case,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
    )


def read_records(path: str | Path, *, max_bytes: int = 10_000_000) -> list[RunRecord]:
    """Read all RunRecords from a JSONL file with input size checks."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    size = os.path.getsize(p)
    if size > max_bytes:
        raise LedgerError("input_too_large", f"File size {size} exceeds limit of {max_bytes} bytes")

    records: list[RunRecord] = []
    with open(p, encoding="utf-8") as f:
        line_num = 0
        for line in f:
            line_num += 1
            cleaned = line.strip()
            if not cleaned:
                continue
            try:
                parsed = json.loads(cleaned)
            except Exception as exc:
                raise LedgerError("corrupt_line", "JSON parse error", line=line_num) from exc
            record = _parse_record_dict(parsed, line_num)
            records.append(record)

    return records
