"""Runtime configuration and constants for the Gmail audit tool."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Final, List


logger = logging.getLogger(__name__)

SCOPES: Final[List[str]] = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PATH: Final[Path] = Path("token.json")
CREDENTIALS_PATH: Final[Path] = Path("credentials.json")
OUTPUT_CSV_PATH: Final[Path] = Path("sites_from_gmail.csv")
CATEGORIES_YAML_PATH: Final[Path] = Path("categories.yml")
SITES_CATALOG_CSV_PATH: Final[Path] = Path("sites_catalog.csv")

# 登録/認証/Welcome 系に寄せたデフォルト検索クエリ
DEFAULT_GMAIL_QUERY: Final[str] = (
    "in:anywhere ("
    "subject:(welcome OR verify OR verification OR confirm OR confirmation "
    "OR 登録 OR 認証 OR 認証コード OR アカウント OR パスワード) "
    "OR \"confirm your email\" OR \"verify your email\""
    ")"
)

# 環境変数 GMAIL_QUERY で上書き可能
GMAIL_QUERY: Final[str] = ""  # 後段で初期化


def get_env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("環境変数 %s は整数として解釈できませんでした。default=%d を使用します", name, default)
        return default


def get_env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


# 最後に GMAIL_QUERY を環境変数で初期化
GMAIL_QUERY = get_env_str("GMAIL_QUERY", DEFAULT_GMAIL_QUERY)
