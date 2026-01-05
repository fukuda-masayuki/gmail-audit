"""Authentication utilities for Gmail API access."""

from __future__ import annotations

import logging
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from . import config


logger = logging.getLogger(__name__)


def get_credentials() -> Credentials:
    """Obtain Gmail API credentials using token.json.

    本番/実行時専用の認証ヘルパーです。

    - 初回 OAuth フローはここでは行いません
    - ローカル等であらかじめ `token.json` を生成しておくことを前提とします
    """

    if not config.TOKEN_PATH.exists():
        raise RuntimeError(
            "token.json が存在しません。ローカル環境などで初回 OAuth フローを実行して "
            "token.json を生成してから実行してください。"
        )

    logger.info("既存の token.json から認証情報を読み込みます")
    creds: Optional[Credentials] = Credentials.from_authorized_user_file(
        str(config.TOKEN_PATH), config.SCOPES
    )

    if creds and creds.expired and creds.refresh_token:
        logger.info("アクセストークンをリフレッシュします")
        creds.refresh(Request())

    if not creds or not creds.valid:
        raise RuntimeError("token.json から有効な認証情報を取得できませんでした。")

    return creds
