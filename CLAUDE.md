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
  - batch/CLAUDE.md: バッチ開発ガイド

## ワークフロー一覧

| ワークフロー | スケジュール | 説明 |
|-------------|-------------|------|
| Sync Members | 毎時 0 分 | サイトメンバー同期、退会検出 |
| Sync Pages | 毎時 | ページデータ同期、discussion_id 更新 |
| Sync Votes | 15 分毎 | 投票データ同期（scp-jp のみ） |
| Sync Forum | 毎時 | フォーラムデータ同期 |
| Detect Deleted | 毎日 03:00 JST | 削除ページ検出 |
| Sync Applications | 15 分毎 | 参加申請同期、自動承認 |
| Sync Algolia | Sync Pages/Forum 完了後 | 検索インデックス同期 |

詳細: .github/workflows/ 配下参照

## 仕組み

1. Deploy Key を使用して panopticon（private）を clone
2. panopticon/batch 配下のスクリプトを実行
3. Panopticon API 経由でデータを同期

## 注意事項

- スクリプト本体は panopticon リポジトリで管理
- このリポジトリはワークフロー定義とスケジュール設定のみ
- スクリプトの修正は panopticon リポジトリで行う
