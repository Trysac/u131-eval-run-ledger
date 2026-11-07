"""Custom exceptions for eval_run_ledger."""

from __future__ import annotations

from typing import Literal

LedgerErrorCode = Literal[
    "invalid_cost",
    "invalid_tokens",
    "invalid_run_id",
    "already_finished",
    "naive_datetime",
    "clock_went_backwards",
    "corrupt_line",
    "input_too_large",
]


class LedgerError(Exception):
    """Base exception raised for all ledger errors."""

    def __init__(
        self,
        code: LedgerErrorCode,
        message: str | None = None,
        *,
        line: int | None = None,
    ) -> None:
        self.code: LedgerErrorCode = code
        self.line: int | None = line
        msg = message or f"Ledger error [{code}]"
        if line is not None:
            msg = f"{msg} (line {line})"
        super().__init__(msg[:200])
