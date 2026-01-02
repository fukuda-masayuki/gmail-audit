"""CSV export helpers."""

from __future__ import annotations

import logging
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import pandas as pd

from .domain import DomainRecord


logger = logging.getLogger(__name__)


def save_to_csv(records: Iterable[DomainRecord], path: Path) -> None:
    records = list(records)
    columns = ["domain", "count", "sample_from", "sample_subject", "sample_list_id"]

    if not records:
        df = pd.DataFrame(columns=columns)
        df.to_csv(path, index=False)
        logger.info("%s を出力しました (行数=0)", path)
        return

    df = pd.DataFrame([asdict(record) for record in records], columns=columns)
    df = df.sort_values(by=["count", "domain"], ascending=[False, True])
    df.to_csv(path, index=False)
    logger.info("%s を出力しました (行数=%d)", path, len(df))
