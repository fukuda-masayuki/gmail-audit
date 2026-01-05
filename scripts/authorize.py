"""ローカル専用: 初回 OAuth フローを実行して token.json を生成するスクリプト。

本番環境（GCP など）にはデプロイせず、ローカル／開発環境のみで利用することを想定しています。
"""

from __future__ import annotations

import logging

from google_auth_oauthlib.flow import InstalledAppFlow

from gmail_audit import config


logger = logging.getLogger(__name__)


def run_interactive_oauth() -> None:
    """ローカルでブラウザベースの OAuth フローを実行し、token.json を生成する。"""

    if not config.CREDENTIALS_PATH.exists():
        raise FileNotFoundError(
            "credentials.json が見つかりません。Google Cloud Console からダウンロードし、"
            "プロジェクト直下に配置してください。",
        )

    # Google のポリシーにより、リダイレクト URI として許可されるのは
    # localhost / 127.0.0.1 のループバックアドレスのみを想定する
    host = config.get_env_str("OAUTH_HOST", "localhost")
    port = config.get_env_int("OAUTH_PORT", 8080)

    logger.info("初回認証フローを開始します (host=%s, port=%d)", host, port)

    flow = InstalledAppFlow.from_client_secrets_file(
        str(config.CREDENTIALS_PATH),
        config.SCOPES,
    )
    creds = flow.run_local_server(host=host, port=port, open_browser=False)

    logger.info("認証完了。token.json に保存します")
    config.TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s - %(message)s",
    )
    run_interactive_oauth()
