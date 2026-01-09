# panopticon-batch

Panopticon バッチ処理用ワークフローリポジトリ

## 概要

このリポジトリは [panopticon](https://github.com/scp-jp/panopticon) のバッチ処理を実行するための GitHub Actions ワークフローを管理する。

Public リポジトリとして運用することで、GitHub Actions を無料で利用可能にしている。

## ワークフロー一覧

| ワークフロー | スケジュール | 説明 |
|-------------|-------------|------|
| Sync Members | 毎時 0 分 | サイトメンバーを同期、退会検出 |
| Sync Pages | 3 時間毎 | ページデータを同期、削除検出、discussion_id 更新 |
| Sync Votes | 30 分毎 | 投票データを同期（scp-jp のみ） |
| Sync Forum | 3 時間毎 | フォーラムデータを同期 |
| Sync Applications | 毎時 0 分 | 参加申請を同期、自動承認 |
| Sync Algolia | Sync Pages/Forum 完了後 | Algolia 検索インデックスを同期 |

## 仕組み

1. Deploy Key を使用して panopticon（private）を clone
2. panopticon/batch 配下のスクリプトを実行
3. Panopticon API 経由でデータを同期

## 必要な Secrets

| Secret 名 | 説明 |
|----------|------|
| `PANOPTICON_DEPLOY_KEY` | panopticon リポジトリへの読み取り専用 SSH キー |
| `PANOPTICON_API_URL` | Panopticon API エンドポイント |
| `PANOPTICON_API_KEY` | Panopticon API キー |
| `WIKIDOT_USERNAME` | Wikidot ユーザー名 |
| `WIKIDOT_PASSWORD` | Wikidot パスワード |
| `ALGOLIA_ADMIN_API_KEY` | Algolia 管理 API キー |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare アカウント ID |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API トークン |
| `DISCORD_WEBHOOK_URL` | Discord 通知用 Webhook URL |
