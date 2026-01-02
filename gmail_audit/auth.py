"""Authentication utilities for Gmail API access."""

from __future__ import annotations

import logging
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from . import config


logger = logging.getLogger(__name__)


def get_credentials() -> Credentials:
    """Obtain Gmail API credentials using credentials.json/token.json."""

    creds: Optional[Credentials] = None

    if config.TOKEN_PATH.exists():
        logger.info("既存の token.json から認証情報を読み込みます")
        creds = Credentials.from_authorized_user_file(str(config.TOKEN_PATH), config.SCOPES)

    if creds and creds.expired and creds.refresh_token:
        logger.info("アクセストークンをリフレッシュします")
        creds.refresh(Request())
        return creds

    if creds and creds.valid:
        return creds

    if not config.CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            "credentials.json が見つかりません。Google Cloud Console からダウンロードし、プロジェクト直下に配置してください。"
        )

    host = config.get_env_str("OAUTH_HOST", "localhost")
    port = config.get_env_int("OAUTH_PORT", 8080)

    logger.info("初回認証フローを開始します (host=%s, port=%d)", host, port)
    flow = InstalledAppFlow.from_client_secrets_file(str(config.CREDENTIALS_PATH), config.SCOPES)
    creds = flow.run_local_server(host=host, port=port, open_browser=False)

    logger.info("認証完了。token.json に保存します")
    config.TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return creds
