"""Append-only JSONL ledger of evaluation runs."""

from __future__ import annotations

import logging

from eval_run_ledger.errors import LedgerError, LedgerErrorCode
from eval_run_ledger.ledger import (
    Run,
    RunRecord,
    append_record,
    read_records,
    start_run,
)

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.0"
__all__ = [
    "LedgerError",
    "LedgerErrorCode",
    "Run",
    "RunRecord",
    "append_record",
    "read_records",
    "start_run",
]
