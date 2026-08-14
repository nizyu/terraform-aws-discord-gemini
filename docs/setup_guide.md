# Discord Gemini Bot セットアップガイド

本ガイドでは、Discord Developer Portalでのアプリケーション作成から、Terraformを用いたAWSリソースのデプロイ、スラッシュコマンドの登録、Discordでの動作確認までの一連の手順を解説します。

---

## 0. 事前準備・必要なもの

1. **Discord アカウント** (Botを導入するサーバーの管理者権限)
2. **Google AI Studio (Gemini) API Key** ([Google AI Studio](https://aistudio.google.com/) から取得)
3. **AWS アカウント** (Administrator または Lambda/DynamoDB/IAM を操作可能な権限)
4. **ローカル環境**:
   - Terraform (`>= 1.5.0`)
   - Python (`>= 3.12`) および pip
   - AWS CLI (認証情報設定済み `aws configure`)

---

## 1. Discord Developer Portal の設定

### 1.1 Discord アプリケーションの作成
1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセスしてログインします。
2. 右上の **「New Application」** をクリックします。
3. アプリ名（例: `Family-Gemini-Bot`）を入力し、規約に同意して **「Create」** をクリックします。

### 1.2 必要な認証情報の取得
1. **General Information 画面**:
   - **APPLICATION ID** をコピーしてメモします（Terraformの `discord_application_id` で使用）。
   - **PUBLIC KEY** をコピーしてメモします（Terraformの `discord_public_key` で使用）。
2. **Bot 画面** (左メニューの「Bot」):
   - **「Reset Token」** をクリックして **TOKEN** を発行・コピーしてメモします（Terraformの `discord_bot_token` およびコマンド登録で使用）。
   - ※このトークンは再表示できないため、安全な場所に保管してください。
   - **Privileged Gateway Intents** は、スラッシュコマンド (HTTP Interactions) のみの運用の場合は **すべて無効 (デフォルト)** のままで問題ありません。

### 1.3 OAuth2 URL Generator で Bot をサーバーに招待
1. 左メニューの **「OAuth2」 > 「URL Generator」** を開きます。
2. **SCOPES** で以下を選択します:
   - `bot`
   - `applications.commands`
3. **BOT PERMISSIONS** で以下を選択します:
   - `Send Messages` (メッセージ送信)
   - `Create Public Threads` (公開スレッドの作成)
   - `Send Messages in Threads` (スレッド内でのメッセージ送信)
   - `Read Message History` (メッセージ履歴の閲覧)
   - `Embed Links` (リンク埋め込み)
4. 画面最下部に生成された **GENERATED URL** をブラウザで開き、Botを導入したいDiscordサーバーを選択して **「認証」** します。

---

## 2. Google Gemini API キーの取得

1. [Google AI Studio](https://aistudio.google.com/) にアクセスします。
2. **「Get API key」** をクリックし、新しい API キーを作成します。
3. 発行された API キーをコピーしてメモします（Terraformの `gemini_api_key` で使用）。

---

## 3. Terraform による AWS デプロイ

### 3.1 tfvars ファイルの準備
`examples/basic/` ディレクトリに移動し、設定ファイルを作成します。

```bash
cd examples/basic
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars` を開き、取得した値を設定します:

```hcl
aws_region             = "ap-northeast-1"
discord_application_id = "YOUR_DISCORD_APPLICATION_ID"
discord_public_key     = "YOUR_DISCORD_PUBLIC_KEY"
discord_bot_token      = "YOUR_DISCORD_BOT_TOKEN"
gemini_api_key         = "YOUR_GEMINI_API_KEY"
gemini_model           = "gemini-3.7-flash"
```

### 3.2 Terraform の初期化と適用
本モジュールは、**GitHub Releases からビルド済み Lambda パッケージ（`ingress.zip`, `worker.zip`）を自動ダウンロード** します。利用者の PC への Python / pip のインストールや手動ダウンロードは不要です。

インフラのデプロイを実行します:

```bash
cd examples/basic
terraform init
terraform apply
```

確認プロンプトで `yes` を入力します。

> [!TIP]
> **バージョンの指定やローカルビルドを使用する場合**:
> - デフォルトでは `release_tag = "v1.0.0"` のリリースアセットが自動ダウンロードされます。特定のバージョンを指定したい場合は `release_tag = "vX.Y.Z"` を指定してください。
> - 自身でソースコードを変更してローカルビルドしたい場合は、`python3 scripts/package.py` でビルドした zip のパスを `ingress_zip_path` / `worker_zip_path` に指定することも可能です。

### 3.3 Interactions Endpoint URL の取得
デプロイが完了すると、Outputs に以下のような Function URL が表示されます:

```text
discord_interactions_endpoint_url = "https://xxxxxx.lambda-url.ap-northeast-1.on.aws/"
```

この URL をコピーします。

---

## 4. Discord への Interactions Endpoint URL 登録

1. [Discord Developer Portal](https://discord.com/developers/applications) に戻り、作成したアプリを開きます。
2. **「General Information」** 画面を開きます。
3. **「INTERACTIONS ENDPOINT URL」** の入力欄に、先ほど取得した Lambda Function URL を貼り付けます。
4. **「Save Changes」** をクリックします。
   - ※Discord から Lambda へ署名検証用の PING リクエストが送信され、自動で検証されます。緑色の「All Changes Saved」が表示されれば成功です。

---

## 5. スラッシュコマンド (`/ask`) の登録

提供されている Python スクリプトを実行して、Discord に `/ask` コマンドを登録します。

### 5.1 登録スクリプトの実行

```bash
# プロジェクトルートに移動
cd ../..

# 必要なライブラリをインストール
pip install requests

# コマンド登録 (全サーバー向けグローバル登録)
python scripts/register_commands.py \
  --application-id YOUR_DISCORD_APPLICATION_ID \
  --bot-token YOUR_DISCORD_BOT_TOKEN
```

> [!TIP]
> **ギルド（サーバー）限定登録をする場合**:
> グローバル登録は反映に数分〜最大1時間程度かかる場合があります。特定のサーバーですぐにテストしたい場合は、`--guild-id YOUR_GUILD_ID` を指定してください（即時反映されます）。
> ```bash
> python scripts/register_commands.py \
>   --application-id YOUR_DISCORD_APPLICATION_ID \
>   --bot-token YOUR_DISCORD_BOT_TOKEN \
>   --guild-id YOUR_GUILD_ID
> ```

---

## 6. 動作確認

1. **親チャンネルで実行**:
   - チャンネルで `/ask prompt:こんにちは！自己紹介をしてください` と入力して送信します。
   - Bot が「考え中...」と表示した後、新しいスレッドが自動作成され、そのスレッド内に Gemini からの返信が投稿されます。
2. **スレッド内で継続して会話**:
   - 作成されたスレッド内で `/ask prompt:さっきの話をもう少し詳しく教えて` と入力して送信します。
   - 前回の会話を踏まえた回答がスレッド内に返信されます。

---

## 7. トラブルシューティング

| 症状 | 原因と対策 |
| :--- | :--- |
| **Endpoint URL 保存時に「Validation failed」エラー** | `discord_public_key` が正しく設定されているか確認してください。また、Lambda Ingress の CloudWatch Logs を確認してください。 |
| **`/ask` コマンドが Discord 上に表示されない** | グローバル登録の場合、Discord 側のキャッシュで反映に時間がかかります。Discord クライアントを再起動（Ctrl+R / Cmd+R）するか、Guild ID を指定して即時登録してください。 |
| **Bot が「考え中...」のまま更新されない** | 後段 Lambda (Worker) の CloudWatch Logs を確認してください。Gemini API Key の権限エラーや、Bot Token の権限不足（Send Messages in Threads 等）がないか確認してください。 |
| **過去の会話履歴が参照されない** | 7日間の TTL が経過してレコードが削除されたか、スレッド外の別チャンネルで実行されている可能性があります。 |
