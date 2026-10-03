# CLAUDE.md

## 概要

Panopticon バッチ処理ワークフローリポジトリ（GitHub Actions）

panopticonリポジトリのbatch/scriptsをGHAで実行するためのワークフロー定義。
Publicリポジトリとして運用（GitHub Actions 無料利用のため）。

## 変数

MEMORY_DIR=.local/
BASE_BRANCH=main

## 関連リポジトリ

- panopticon（private）: メイン開発リポジトリ
  - batch/scripts/: 実行されるPythonスクリプト
  - batch/lib/: 共通ライブラリ
  - batch/CLAUDE.md: バッチ開発ガイド（Wikidot API特性、増分同期の仕組み等）

## ワークフロー一覧

定期起動は panopticon の apps/sync（Worker `panopticon-sync`）が `workflow_dispatch` で行う（各 workflow に `schedule:` は無い）。
ジョブごとの起動先（`gha` / `workers` / `paused`）は panopticon の site DB の `sync_job_settings` で切り替える（panopticon の `apps/sync/CLAUDE.md`）。

| ワークフロー | 起動（`gha` のとき、UTC） | 説明 |
|-------------|-------------|------|
| Sync Pages | 偶数時 :00 | ページ/リビジョン/ファイル同期 → discussion_id更新 → Sync Votesチェーン |
| Sync Forum | 偶数時 :00 | フォーラムカテゴリ/スレッド/投稿同期 |
| Sync Votes | 毎時 :30 | 投票データ同期（scp-jpのみ、--only-votesモード） |
| Sync Members | 02/08/14/20時 :00 | サイトメンバー同期 |
| Sync Applications | :00 / :30 | 参加申請同期 |
| Detect Deleted | 18:00（03:00 JST） | 削除ページ検出 |
| Sync Algolia | Sync Pages/Forum完了後 | 検索インデックス同期（workflow_runトリガー） |
| Monitor Workflow Health | 月曜 00:00（`schedule:`） | 無効化された workflow と最終コミットからの日数を Discord に通知 |

apps/sync へ切り替えたジョブの workflow は無効にし、リポジトリの Variables `INTENTIONALLY_DISABLED_WORKFLOWS`（ファイル名を空白区切り）に足す。
足さないと Monitor Workflow Health が毎週 CRITICAL を出す。

## 仕組み

1. Deploy Keyを使用してpanopticon（private）をclone
2. panopticon/batch配下のスクリプトを実行
3. Panopticon API経由でデータを同期

## GHA実行環境の制約

### ランナー環境

- **Azure Region: eastus**（US東海岸）
- Wikidot APIへの接続が不安定（日本からのローカル実行と比較して大幅に劣る）
- `attempt_limit=15`（panopticon側で設定済み）で対応

### 適用済みの対策

| 対策 | 設定箇所 | 値 |
|------|---------|-----|
| attempt_limit | panopticon/batch/lib/config.py | 15（デフォルト5→15） |
| concurrency | sync-pages.yml, sync-forum.yml | 5（`--concurrency 5`） |
| chunk-size | sync-pages.yml | 25（`--chunk-size 25`、初回・リトライ両方） |
| 自動リトライ | sync-pages.yml, sync-forum.yml | 失敗時に30秒待機後 `--retry-failed` 実行 |
| リトライ時concurrency | panopticon/batch/scripts/ | 自動で3に低減（`--concurrency`未指定時） |

### 大量データ回復時の方針

GHAではなくローカル（日本）で実行する方が確実。理由:
- attempt_limit=5でもエラーゼロ（リトライのオーバーヘッドがない）
- GHAの6時間ジョブタイムアウトの心配がない
- `--full` や大きな `SYNC_MARGIN_DAYS` での実行に適している

```bash
# ローカル実行例
git clone git@github.com:SCP-JP/panopticon.git
cd panopticon/batch
uv sync
# .env を作成（PANOPTICON_API_URL, PANOPTICON_API_KEY, WIKIDOT_USERNAME, WIKIDOT_PASSWORD）

# Pages回復（50日分遡り）
SYNC_MARGIN_DAYS=50 uv run scripts/sync_pages.py --concurrency 5 --no-cache --chunk-size 25 scp-jp

# Forum回復（全件再取得が必要）
uv run scripts/sync_forum.py --concurrency 5 --no-cache --full --chunk-size 25 scp-jp
```

## 注意事項

- スクリプト本体はpanopticonリポジトリで管理。このリポジトリはワークフロー定義とスケジュール設定のみ
- 定期起動を止める場合は panopticon の `sync_job_settings` で該当ジョブを `paused` にする（Sync Algoliaはworkflow_runなので自動停止）
- `test-wikidot-params.yml` はWikidot APIパラメータのテスト用ワークフロー（手動実行のみ）
