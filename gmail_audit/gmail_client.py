"""Thin wrapper around the Gmail API client."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .config import GMAIL_QUERY


logger = logging.getLogger(__name__)


def build_gmail_service(creds: Credentials):
    return build("gmail", "v1", credentials=creds)


class GmailClient:
    """Encapsulates Gmail API interactions."""

    def __init__(self, service) -> None:
        self._service = service

    def list_message_ids(self, max_messages: int) -> List[str]:
        logger.info("Gmail メッセージを検索します (max_messages=%d)", max_messages)

        collected: List[str] = []
        page_token: Optional[str] = None

        while len(collected) < max_messages:
            remaining = max_messages - len(collected)
            resp = (
                self._service.users()
                .messages()
                .list(
                    userId="me",
                    q=GMAIL_QUERY,
                    maxResults=min(500, remaining),
                    pageToken=page_token,
                )
                .execute()
            )

            messages = resp.get("messages", [])
            if not messages:
                break

            for message in messages:
                collected.append(message["id"])
                if len(collected) >= max_messages:
                    break

            page_token = resp.get("nextPageToken")
            if not page_token:
                break

        logger.info("メッセージIDを %d 件取得しました", len(collected))
        return collected

    def get_message_headers(self, message_id: str) -> List[Dict[str, str]]:
        resp = (
            self._service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="metadata",
                metadataHeaders=["From", "Reply-To", "Subject", "Date", "List-Id"],
            )
            .execute()
        )
        payload = resp.get("payload", {})
        return payload.get("headers", [])
