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

### 1. Gmail スキャン（sites_from_gmail.csv 作成）

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

### 3. カタログ生成（sites_catalog.csv 作成）

Gmail スキャン後、下記コマンドでカテゴリ付きカタログ `sites_catalog.csv` を生成します。

```bash
poetry run python catalog.py
```

初回実行時に `categories.yml` が存在しない場合、サンプル入りの雛形を自動生成します。

## コード構成

- [gmail_audit/config.py](gmail_audit/config.py): 環境変数や定数の定義
- [gmail_audit/auth.py](gmail_audit/auth.py): OAuth 認証フローの実装
- [gmail_audit/gmail_client.py](gmail_audit/gmail_client.py): Gmail API クライアントの薄いラッパー
- [gmail_audit/domain.py](gmail_audit/domain.py): ドメイン抽出ロジックとデータモデル
- [gmail_audit/aggregator.py](gmail_audit/aggregator.py): メール単位の集計処理
- [gmail_audit/output.py](gmail_audit/output.py): CSV 出力処理
- [gmail_audit/main.py](gmail_audit/main.py): 上記を組み合わせたエントリポイント
- [gmail_audit/catalog.py](gmail_audit/catalog.py): `sites_from_gmail.csv` を読み取り、カテゴリ付き `sites_catalog.csv` を生成

## 環境変数

- `MAX_MESSAGES` (デフォルト: 500)
  - Gmail 検索結果から最大何件までメッセージを取得するか
- `OAUTH_HOST` (デフォルト: localhost)
  - OAuth ローカルサーバのバインドアドレス
- `OAUTH_PORT` (デフォルト: 8080)
  - OAuth ローカルサーバの待ち受けポート
- `GMAIL_QUERY`
  - Gmail の検索クエリを上書きしたい場合に指定する
  - 未指定時は、登録/認証/Welcome 系に寄せたデフォルトクエリを使用する

## 出力ファイル

- `sites_from_gmail.csv`
  - `domain`: eTLD+1 に正規化したドメイン (例: `a.b.example.co.jp` → `example.co.jp`)
  - `count`: 観測メッセージ数
  - `sample_from`: サンプルの From / Reply-To
  - `sample_subject`: サンプルの Subject
  - `sample_list_id`: List-Id が取得できた場合のサンプル値
- `sites_catalog.csv`
  - `service_name`: ドメインから推測したサービス名（Title Case）
  - `category`: `categories.yml` またはルールに基づくカテゴリ
  - `source`: `dict` (辞書命中) / `rule` (件名ルール) / `unknown`
  - `notes`: 予備欄（現状は空）

`categories.yml` を編集することで任意のドメインにカテゴリを手動で割り当てられます。辞書に無いドメインは件名キーワード（newsletter / unsubscribe / メルマガ / 配信停止 → `newsletter`、receipt / invoice / 領収書 / ご注文 / 配送 / shipped → `transaction`）で推定され、該当しなければ `unknown` になります。

## 注意事項

- `credentials.json` と `token.json` は機密情報のため、必ず `.gitignore` による除外を行ってください
- このツールは PoC であり、メールが来ないサービスは検出できません
- メール本文は扱わず、ヘッダー情報のみを利用しています
# gmail-audit
