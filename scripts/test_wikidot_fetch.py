"""Wikidot API取得テスト

APIからのデータ取得のみ実行し、エラー発生状況を確認する。
Panopticon APIへの投入は一切行わない。

Usage:
    uv run scripts/test_wikidot_fetch.py [site] [--concurrency N] [--limit N]
        [--timeout N] [--attempt-limit N] [--skip-source]
"""

import argparse
import logging
import os
import sys
import time

# panopticon/batch の依存関係を使うため、パス追加不要（uv run で実行）

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Wikidot API取得テスト")
    parser.add_argument("site", nargs="?", default="scp-jp-sandbox3", help="対象サイト")
    parser.add_argument("--concurrency", type=int, default=5, help="並列度 (semaphore_limit)")
    parser.add_argument("--limit", type=int, default=50, help="取得ページ数上限")
    parser.add_argument("--timeout", type=int, default=20, help="リクエストタイムアウト(秒)")
    parser.add_argument("--attempt-limit", type=int, default=5, help="リトライ上限回数")
    parser.add_argument("--skip-source", action="store_true", help="ソース取得をスキップ")
    args = parser.parse_args()

    username = os.environ.get("WIKIDOT_USERNAME")
    password = os.environ.get("WIKIDOT_PASSWORD")

    if not username or not password:
        logger.error("WIKIDOT_USERNAME, WIKIDOT_PASSWORD を設定してください")
        sys.exit(1)

    # wikidotライブラリのログを全レベル表示（リトライ等のINFOも見る）
    logging.getLogger("wikidot").setLevel(logging.DEBUG)
    # httpxのリクエストログは抑制
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger.info("=" * 60)
    logger.info("Wikidot API取得テスト")
    logger.info("=" * 60)
    logger.info(f"  サイト:          {args.site}")
    logger.info(f"  並列度:          {args.concurrency}")
    logger.info(f"  タイムアウト:    {args.timeout}秒")
    logger.info(f"  リトライ上限:    {args.attempt_limit}回")
    logger.info(f"  ページ上限:      {args.limit}")
    logger.info(f"  ソース取得:      {'スキップ' if args.skip_source else '実行'}")
    logger.info("=" * 60)

    from wikidot import Client as WikidotClient
    from wikidot.connector.ajax import AjaxModuleConnectorConfig

    amc_config = AjaxModuleConnectorConfig(
        semaphore_limit=args.concurrency,
        request_timeout=args.timeout,
        attempt_limit=args.attempt_limit,
    )

    client = WikidotClient(username=username, password=password, amc_config=amc_config)

    with client:
        site = client.site.get(args.site)
        logger.info(f"サイト接続OK: {args.site}")

        # Step 1: ページリスト取得
        logger.info("")
        logger.info("--- Step 1: ページリスト取得 ---")
        t0 = time.time()
        pages = site.pages.search(
            category="*",
            order="updated_at desc",
            limit=args.limit,
        )
        elapsed = time.time() - t0
        logger.info(f"ページリスト: {len(pages)}件 ({elapsed:.1f}秒)")

        # Step 2: ページID取得
        logger.info("")
        logger.info("--- Step 2: ページID取得 ---")
        t0 = time.time()
        try:
            pages.get_page_ids()
            elapsed = time.time() - t0
            logger.info(f"ページID取得OK: {len(pages)}件 ({elapsed:.1f}秒)")
        except Exception as e:
            elapsed = time.time() - t0
            logger.error(f"ページID取得失敗 ({elapsed:.1f}秒): {e}")
            sys.exit(1)

        # Step 3: リビジョン一覧取得
        logger.info("")
        logger.info("--- Step 3: リビジョン一覧取得 ---")
        success_rev = 0
        fail_rev = 0
        t0 = time.time()
        for i, page in enumerate(pages):
            try:
                revs = page.revisions
                rev_count = len(revs) if revs else 0
                success_rev += 1
                if (i + 1) % 10 == 0:
                    logger.info(
                        f"  [{i+1}/{len(pages)}] {page.fullname}: "
                        f"{rev_count}リビジョン OK"
                    )
            except Exception as e:
                fail_rev += 1
                logger.error(
                    f"  [{i+1}/{len(pages)}] {page.fullname}: "
                    f"リビジョン取得失敗: {type(e).__name__}: {e}"
                )
        elapsed = time.time() - t0
        logger.info(f"リビジョン一覧: 成功{success_rev} 失敗{fail_rev} ({elapsed:.1f}秒)")

        # Step 4: ソース取得
        success_src = 0
        fail_src = 0
        total_revs = 0
        if not args.skip_source:
            logger.info("")
            logger.info("--- Step 4: リビジョンソース取得 ---")
            t0 = time.time()
            for i, page in enumerate(pages):
                try:
                    revs = page.revisions
                    if not revs:
                        continue
                    total_revs += len(revs)
                    revs.get_sources()
                    success_src += 1
                    if (i + 1) % 10 == 0:
                        logger.info(
                            f"  [{i+1}/{len(pages)}] {page.fullname}: "
                            f"{len(revs)}リビジョンのソース取得OK"
                        )
                except Exception as e:
                    fail_src += 1
                    logger.error(
                        f"  [{i+1}/{len(pages)}] {page.fullname}: "
                        f"ソース取得失敗: {type(e).__name__}: {e}"
                    )
            elapsed = time.time() - t0
            logger.info(
                f"ソース取得: 成功{success_src}ページ 失敗{fail_src}ページ "
                f"(リビジョン計{total_revs}件, {elapsed:.1f}秒)"
            )

    # サマリー
    logger.info("")
    logger.info("=" * 60)
    logger.info("結果サマリー")
    logger.info("=" * 60)
    logger.info(f"  設定: timeout={args.timeout}s, attempts={args.attempt_limit}, concurrency={args.concurrency}")
    logger.info(f"  ページ: {len(pages)}件取得")
    logger.info(f"  リビジョン一覧: 成功{success_rev} 失敗{fail_rev}")
    if not args.skip_source:
        logger.info(f"  ソース取得: 成功{success_src} 失敗{fail_src} (計{total_revs}rev)")
    has_errors = fail_rev > 0 or (not args.skip_source and fail_src > 0)
    logger.info(f"  総合: {'ERROR' if has_errors else 'OK'}")
    logger.info("=" * 60)

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
