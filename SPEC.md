# Gmail登録サイト棚卸しツール 仕様（SPEC）

## 1. 目的
Gmail全体から「アカウント登録/認証/Welcome系メール」を手掛かりに、
利用しているサイト/サービスの候補をドメイン単位で抽出し、一覧化する。
その後、ジャンル（カテゴリ）分けを行う。

## 2. スコープ（今回）
- Gmail API を OAuth（個人アカウント）で読み取り（readonly）
- Gmail検索（q）で登録系メールを抽出
- メール本文は扱わず、ヘッダー（metadata）中心でドメインを抽出
- ドメインをユニーク化し、CSVに出力する

## 3. 非スコープ（今回やらない）
- 完全網羅の保証（メールが来ないサービスは検出できない）
- 画面UI
- リアルタイム（Push通知 / watch）
- Cloud Run本番デプロイ（後続で実施）

## 4. 期待成果物（PoCのゴール）
- `sites_from_gmail.csv` を生成する
  - domain: eTLD+1 へ正規化したドメイン（例: mail.foo.example.com → example.com）
  - count: 観測数
  - sample_from: サンプルFrom（またはReply-To）
  - sample_subject: サンプルSubject
- 登録済みCSVを元にカテゴリ付き `sites_catalog.csv` を生成する

## 5. 技術要件
- 言語: Python 3.12
- 実行環境: Docker（ローカル）
- 依存:
  - google-api-python-client
  - google-auth-oauthlib
  - google-auth-httplib2
  - pandas
  - tldextract

## 6. 認証/権限
- OAuthクライアント: Desktop/Installed
- 利用スコープ: `https://www.googleapis.com/auth/gmail.readonly`
- `credentials.json` をプロジェクト直下に配置
- ローカル専用スクリプト（`scripts/authorize.py`）で初回 OAuth フローを実行し、`token.json` を生成する
- 実行時のコード（`gmail_audit.auth.get_credentials`）は、あらかじめ生成された `token.json` の存在を前提とし、本番環境ではブラウザを開くようなフローは行わない

## 7. データ取得仕様
### 7.1 Gmail検索クエリ（初期案）
- 目的: 登録/認証/Welcome系を優先して拾う
- 例（デフォルトクエリのイメージ）:
  - `in:anywhere (subject:(welcome OR verify OR verification OR confirm OR confirmation OR 登録 OR 認証 OR 認証コード OR アカウント OR パスワード) OR "confirm your email" OR "verify your email")`
- 実際のクエリ文字列は `DEFAULT_GMAIL_QUERY` としてコード側に定義し、環境変数 `GMAIL_QUERY` で上書き可能とする

### 7.2 取得API
- `users.messages.list` で message id を収集
- `users.messages.get`（format=metadata）でヘッダー取得
  - 対象ヘッダー: From, Reply-To, Subject, Date, List-Id

## 8. ドメイン抽出仕様
- 優先順位: Reply-To > From
- From/Reply-To からメールアドレスのドメイン部を抽出
- `tldextract` を用いて eTLD+1 に正規化（例: a.b.example.co.jp → example.co.jp）
- 抽出できない場合はスキップ

## 9. 実行パラメータ（環境変数）
- `MAX_MESSAGES`（default: 500）
- `OAUTH_HOST`（default: localhost）  ※`scripts/authorize.py` が起動する OAuth ローカルサーバのバインドアドレス（Google のポリシー上、localhost/127.0.0.1 のループバックを想定）
- `OAUTH_PORT`（default: 8080）       ※`scripts/authorize.py` が待ち受けるポート

## 10. ローカル実行方法（Docker 想定）
### 10.1 ビルド
- `docker build -t gmail-audit .`

### 10.2 初回 OAuth（ローカル専用）
- `docker run --rm -p 8080:8080 -v "$(pwd):/app" gmail-audit python scripts/authorize.py`

コンソールに認証URLが出る → ブラウザで許可 → `token.json` がボリュームマウント先（例: `$(pwd)`）に作成されることを想定する。

### 10.3 Gmail スキャン実行
- `docker run --rm -v "$(pwd):/app" gmail-audit`

`sites_from_gmail.csv` がボリュームマウント先（例: `$(pwd)`）に生成されることを想定する。

## 11. セキュリティ
- `credentials.json` と `token.json` は絶対にGitへコミットしない
- `.gitignore` に必ず追加する

## 12. 次フェーズ（拡張）
- ノイズ除去（ニュースレター/請求/配送通知など）
- ジャンル分類（辞書 + ルール → 必要ならLLM）
- Cloud Run Jobs化、Schedulerで定期実行
- 将来: HTTPサービス化（入口差し替え）やPush通知対応
