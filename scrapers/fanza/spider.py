"""Fetch FANZA's monthly actress ranking and mirror it into all site locales."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

URL = "https://video.dmm.co.jp/av/ranking/?term=monthly&type=actress"
GRAPHQL_URL = "https://api.video.dmm.co.jp/graphql"
RANKING_OPERATION = "ActressRankingPage"
PAGE_SIZE = 100
MAX_LIMIT = 100
DEFAULT_OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "zh" / "排名"
)


class FanzaActressRankingSpider:
    """FANZA monthly actress-ranking scraper."""

    def __init__(
        self,
        output_dir: str = str(DEFAULT_OUTPUT_DIR),
        proxy: str | None = None,
        playwright_factory: Callable[[], Any] | None = None,
    ) -> None:
        requested = Path(output_dir)
        if not requested.is_absolute():
            requested = Path(__file__).parent / requested
        self.output_dir = requested.resolve()
        self.proxy = proxy
        self.playwright_factory = playwright_factory

    @staticmethod
    def validate_limit(limit: int) -> int:
        if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
            raise ValueError(f"limit must be an integer between 1 and {MAX_LIMIT}")
        return limit

    @staticmethod
    def extract_items(body: object) -> list[dict]:
        """Validate the GraphQL envelope and return its actress-ranking rows."""
        if not isinstance(body, dict):
            raise ValueError("GraphQL response root must be an object")
        errors = body.get("errors")
        if errors:
            raise ValueError(f"GraphQL response contains errors: {errors}")
        data = body.get("data")
        if not isinstance(data, dict):
            raise ValueError("GraphQL response is missing `data`")
        ranking = data.get("ppvActressRanking")
        if not isinstance(ranking, dict):
            raise ValueError("GraphQL response is missing `ppvActressRanking`")
        items = ranking.get("items")
        if not isinstance(items, list):
            raise ValueError("GraphQL response is missing `ppvActressRanking.items`")
        if not all(isinstance(item, dict) for item in items):
            raise ValueError("GraphQL ranking contains a non-object item")
        return items

    @classmethod
    def parse_items(cls, items: list[dict], limit: int) -> list[dict]:
        """Validate and normalize exactly ``limit`` contiguous ranking rows."""
        cls.validate_limit(limit)
        if len(items) < limit:
            raise ValueError(f"expected {limit} ranking rows, received {len(items)}")

        rankings = []
        actress_ids = set()
        for expected_rank, item in enumerate(items[:limit], start=1):
            if item.get("rank") != expected_rank or type(item.get("rank")) is not int:
                raise ValueError(
                    f"ranking row {expected_rank} has invalid rank {item.get('rank')!r}"
                )
            actress = item.get("actress")
            latest = actress.get("latestContent") if isinstance(actress, dict) else None
            if not isinstance(actress, dict) or not isinstance(latest, dict):
                raise ValueError(
                    f"ranking row {expected_rank} has invalid actress data"
                )

            actress_id = actress.get("id")
            name = actress.get("name")
            image = actress.get("imageUrl")
            contents_count = actress.get("contentsCountOnSale")
            latest_content_id = latest.get("id")
            latest_title = latest.get("title")
            if not isinstance(actress_id, str) or not actress_id.strip():
                raise ValueError(f"ranking row {expected_rank} has invalid actress id")
            if actress_id in actress_ids:
                raise ValueError(f"duplicate actress id in ranking: {actress_id}")
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"ranking row {expected_rank} has invalid name")
            if not isinstance(image, str) or not image.strip():
                raise ValueError(f"ranking row {expected_rank} has invalid image URL")
            if type(contents_count) is not int or contents_count < 0:
                raise ValueError(
                    f"ranking row {expected_rank} has invalid contents count"
                )
            if not isinstance(latest_content_id, str) or not latest_content_id.strip():
                raise ValueError(
                    f"ranking row {expected_rank} has invalid latest content id"
                )
            if not isinstance(latest_title, str) or not latest_title.strip():
                raise ValueError(
                    f"ranking row {expected_rank} has invalid latest content title"
                )

            actress_ids.add(actress_id)
            rankings.append(
                {
                    "rank": expected_rank,
                    "actress_id": actress_id,
                    "name": name,
                    "image": image,
                    "contents_count": contents_count,
                    "latest_content_id": latest_content_id,
                    "latest_title": latest_title,
                }
            )
        return rankings

    def is_ranking_response(self, response: Any) -> bool:
        """Return whether a response is the requested monthly ranking query."""
        request = response.request
        if response.url != GRAPHQL_URL or request.method != "POST":
            return False
        try:
            payload = json.loads(request.post_data or "")
        except json.JSONDecodeError:
            return False
        if not isinstance(payload, dict):
            return False
        variables = payload.get("variables")
        return (
            payload.get("operationName") == RANKING_OPERATION
            and isinstance(variables, dict)
            and variables.get("filter") == {"monthly": {"floor": "AV"}}
            and variables.get("limit") == PAGE_SIZE
            and variables.get("offset") == 0
        )

    def fetch_ranking(self, limit: int = PAGE_SIZE) -> list[dict]:
        """Fetch and strictly validate the live monthly ranking response."""
        self.validate_limit(limit)
        if self.playwright_factory is None:
            from playwright.sync_api import sync_playwright

            playwright_factory = sync_playwright
        else:
            playwright_factory = self.playwright_factory

        print(f"Loading: {URL}")
        with playwright_factory() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                proxy={"server": self.proxy} if self.proxy else None,
            )
            try:
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    locale="ja-JP",
                )
                context.add_cookies(
                    [
                        {
                            "name": "age_check_done",
                            "value": "1",
                            "domain": ".dmm.co.jp",
                            "path": "/",
                        },
                        {
                            "name": "adult_check",
                            "value": "done",
                            "domain": ".dmm.co.jp",
                            "path": "/",
                        },
                    ]
                )
                page = context.new_page()
                with page.expect_response(
                    self.is_ranking_response, timeout=60000
                ) as response_info:
                    navigation = page.goto(
                        URL, wait_until="domcontentloaded", timeout=60000
                    )
                if navigation is None or navigation.status >= 400:
                    status = "no response" if navigation is None else navigation.status
                    raise RuntimeError(f"FANZA page navigation failed: {status}")
                if "age_check" in page.url or "adult" in page.url:
                    raise RuntimeError(
                        f"FANZA redirected to an age-verification page: {page.url}"
                    )

                ranking_response = response_info.value
                if ranking_response.status >= 400:
                    raise RuntimeError(
                        f"FANZA GraphQL request failed with HTTP {ranking_response.status}"
                    )
                try:
                    body = ranking_response.json()
                except Exception as exc:
                    raise ValueError(
                        "FANZA GraphQL response is not valid JSON"
                    ) from exc
                items = self.extract_items(body)
                print(f"Captured {len(items)} items from GraphQL API")
                return self.parse_items(items, limit)
            finally:
                browser.close()

    @staticmethod
    def serialize(data: list[dict], fetched_at: datetime) -> bytes:
        output = {
            "source": "FANZA",
            "type": "actress_monthly_ranking",
            "url": URL,
            "fetched_at": fetched_at.isoformat().replace("+00:00", "Z"),
            "count": len(data),
            "rankings": data,
        }
        return yaml.safe_dump(
            output,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ).encode("utf-8")

    def target_directories(self, filename: str) -> list[Path]:
        if Path(filename).name != filename or not filename.endswith(".yaml"):
            raise ValueError("filename must be a plain .yaml filename")
        targets = [self.output_dir]
        if self.output_dir == DEFAULT_OUTPUT_DIR:
            root = DEFAULT_OUTPUT_DIR.parent.parent.parent
            targets.extend(
                [root / "docs" / "ja" / "排名", root / "docs" / "en" / "排名"]
            )
        return targets

    def save_yaml(
        self,
        data: list[dict],
        filename: str | None = None,
        now: datetime | None = None,
    ) -> Path:
        """Serialize once and atomically mirror the ranking to all locales."""
        fetched_at = now or datetime.now(UTC)
        if fetched_at.tzinfo is None:
            raise ValueError("fetched_at must be timezone-aware")
        fetched_at = fetched_at.astimezone(UTC)
        if filename is None:
            filename = f"actress-ranking-{fetched_at.strftime('%Y%m')}.yaml"
        directories = self.target_directories(filename)
        content = self.serialize(data, fetched_at)

        temporary_files = []
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    dir=directory,
                    prefix=f".{filename}.",
                    delete=False,
                ) as temporary:
                    temporary.write(content)
                    temporary.flush()
                    os.fsync(temporary.fileno())
                    temporary_files.append((directory / filename, Path(temporary.name)))
            # Replace translations first and the Chinese source last. Each file is
            # atomic; if preparation fails, no published file has been replaced.
            for destination, temporary in reversed(temporary_files):
                os.replace(temporary, destination)
        finally:
            for _, temporary in temporary_files:
                temporary.unlink(missing_ok=True)

        destination = directories[0] / filename
        print(f"Saved {len(data)} entries to {destination}")
        if len(directories) == 3:
            print("Mirrored ranking to docs/ja/排名 and docs/en/排名")
        return destination

    def run(self, limit: int = PAGE_SIZE) -> Path:
        """Fetch, validate, and save one monthly ranking snapshot."""
        self.validate_limit(limit)
        print(f"Fetching FANZA actress ranking (top {limit})...")
        data = self.fetch_ranking(limit)
        print("\nTop 10:")
        for item in data[:10]:
            print(
                f"  {item['rank']:3d}. {item['name']} "
                f"({item['contents_count']} contents)"
            )
        return self.save_yaml(data)


def parse_limit(value: str) -> int:
    try:
        limit = int(value)
        FanzaActressRankingSpider.validate_limit(limit)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return limit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FANZA actress ranking spider")
    parser.add_argument(
        "--limit", type=parse_limit, default=PAGE_SIZE, help="Number of rows (1-100)"
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Output directory (default: repository docs/zh/排名)",
    )
    parser.add_argument(
        "--proxy",
        default=None,
        help="Optional proxy URL, for example socks5://127.0.0.1:7890",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        spider = FanzaActressRankingSpider(output_dir=args.output, proxy=args.proxy)
        result = spider.run(args.limit)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"\nDone! Saved to {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
