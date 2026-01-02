"""Domain aggregation logic."""

from __future__ import annotations

import logging
from typing import Dict, List

from .domain import DomainRecord, extract_domain_from_headers
from .gmail_client import GmailClient


logger = logging.getLogger(__name__)


def aggregate_domains(client: GmailClient, message_ids: List[str]) -> List[DomainRecord]:
    stats: Dict[str, DomainRecord] = {}

    for index, message_id in enumerate(message_ids, start=1):
        if index % 50 == 0 or index == len(message_ids):
            logger.info("メッセージ %d/%d を処理中", index, len(message_ids))

        try:
            headers = client.get_message_headers(message_id)
        except Exception as exc:  # APIエラー時はスキップ
            logger.warning("message_id=%s の取得に失敗しました: %s", message_id, exc)
            continue

        domain, from_, reply_to, subject = extract_domain_from_headers(headers)
        if not domain:
            continue

        record = stats.get(domain)
        if record is None:
            record = DomainRecord(
                domain=domain,
                sample_from=reply_to or from_ or "",
                sample_subject=subject or "",
            )
            stats[domain] = record

        record.count += 1

    return list(stats.values())
