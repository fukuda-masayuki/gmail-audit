# Gmail登録サイト棚卸しツール

このリポジトリは、Gmail から「アカウント登録/認証/Welcome系メール」を検索し、
ドメイン単位で利用中のサイト/サービス候補を棚卸しする PoC ツールです。

詳細仕様は [SPEC.md](SPEC.md) を参照してください。

## 前提

- Python 3.12
- Poetry (>= 1.6 目安)
- Gmail 個人アカウント
- Gmail API が有効化された Google Cloud プロジェクト
- OAuth クライアント種別: Desktop / Installed
- 取得スコープ: `https://www.googleapis.com/auth/gmail.readonly`

## セットアップ（Poetry）

1. Poetry をインストール
  - `pipx install poetry` など
2. このディレクトリに移動し、依存関係をインストール

```bash
poetry install
```

3. Google Cloud Console で OAuth クライアント (Desktop) を作成
4. そのクライアントの JSON をダウンロードし、プロジェクト直下に `credentials.json` という名前で配置
5. `sites_from_gmail.csv` や `token.json` を Git にコミットしないように注意

## 実行方法

### 1. Poetry 経由でスクリプトを実行

```bash
poetry run python -m gmail_audit.main
```

または、`pyproject.toml` のエントリポイント経由で:

```bash
poetry run gmail-audit
```

### 2. 初回実行時のフロー

1. ターミナルに認可 URL が表示されます
2. その URL をブラウザで開き、Gmail アカウントで許可します
3. リダイレクト先 (デフォルト: `http://localhost:8080`) でフローが完了し、プロジェクト直下に `token.json` が生成されます
4. メールのスキャン完了後、`sites_from_gmail.csv` がカレントディレクトリに出力されます

2 回目以降は `token.json` を再利用するため、ブラウザでの認証は通常不要です。

## コード構成

- [gmail_audit/config.py](gmail_audit/config.py): 環境変数や定数の定義
- [gmail_audit/auth.py](gmail_audit/auth.py): OAuth 認証フローの実装
- [gmail_audit/gmail_client.py](gmail_audit/gmail_client.py): Gmail API クライアントの薄いラッパー
- [gmail_audit/domain.py](gmail_audit/domain.py): ドメイン抽出ロジックとデータモデル
- [gmail_audit/aggregator.py](gmail_audit/aggregator.py): メール単位の集計処理
- [gmail_audit/output.py](gmail_audit/output.py): CSV 出力処理
- [gmail_audit/main.py](gmail_audit/main.py): 上記を組み合わせたエントリポイント

## 環境変数

- `MAX_MESSAGES` (デフォルト: 500)
  - Gmail 検索結果から最大何件までメッセージを取得するか
- `OAUTH_HOST` (デフォルト: localhost)
  - OAuth ローカルサーバのバインドアドレス
- `OAUTH_PORT` (デフォルト: 8080)
  - OAuth ローカルサーバの待ち受けポート

## 出力ファイル

- `sites_from_gmail.csv`
  - `domain`: eTLD+1 に正規化したドメイン (例: `a.b.example.co.jp` → `example.co.jp`)
  - `count`: 観測メッセージ数
  - `sample_from`: サンプルの From / Reply-To
  - `sample_subject`: サンプルの Subject

## 注意事項

- `credentials.json` と `token.json` は機密情報のため、必ず `.gitignore` による除外を行ってください
- このツールは PoC であり、メールが来ないサービスは検出できません
- メール本文は扱わず、ヘッダー情報のみを利用しています
# gmail-audit
