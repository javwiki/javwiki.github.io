from __future__ import annotations

import json
import os
from contextlib import AbstractContextManager
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

from scrapers.fanza import spider as spider_module
from scrapers.fanza.spider import GRAPHQL_URL, FanzaActressRankingSpider


def ranking_items(count: int = 2) -> list[dict]:
    return [
        {
            "rank": rank,
            "actress": {
                "id": str(1000 + rank),
                "name": f"Actress {rank}",
                "imageUrl": f"https://example.test/{rank}.jpg",
                "contentsCountOnSale": rank * 10,
                "latestContent": {
                    "id": f"abc{rank:03d}",
                    "title": f"Title {rank}",
                },
            },
        }
        for rank in range(1, count + 1)
    ]


def test_default_connection_is_direct_and_limit_is_bounded() -> None:
    spider = FanzaActressRankingSpider()

    assert spider.proxy is None
    assert spider.validate_limit(1) == 1
    assert spider.validate_limit(100) == 100
    for invalid in (0, -1, 101, True, "1"):
        with pytest.raises(ValueError):
            spider.validate_limit(invalid)  # type: ignore[arg-type]


def test_graphql_envelope_is_strict() -> None:
    assert (
        len(
            FanzaActressRankingSpider.extract_items(
                {"data": {"ppvActressRanking": {"items": ranking_items()}}}
            )
        )
        == 2
    )

    for invalid in (
        [],
        {"errors": [{"message": "failed"}]},
        {"data": None},
        {"data": {}},
        {"data": {"ppvActressRanking": {"items": "bad"}}},
        {"data": {"ppvActressRanking": {"items": ["bad"]}}},
    ):
        with pytest.raises(ValueError):
            FanzaActressRankingSpider.extract_items(invalid)


def test_parse_items_requires_contiguous_unique_rows() -> None:
    parsed = FanzaActressRankingSpider.parse_items(ranking_items(), 2)
    assert [item["rank"] for item in parsed] == [1, 2]

    items = ranking_items()
    items[1]["rank"] = 3
    with pytest.raises(ValueError, match="invalid rank"):
        FanzaActressRankingSpider.parse_items(items, 2)

    items = ranking_items()
    items[1]["actress"]["id"] = items[0]["actress"]["id"]
    with pytest.raises(ValueError, match="duplicate actress"):
        FanzaActressRankingSpider.parse_items(items, 2)

    with pytest.raises(ValueError, match="expected 2"):
        FanzaActressRankingSpider.parse_items(ranking_items(1), 2)


def test_ranking_response_predicate_matches_only_target_operation() -> None:
    def response(operation: str = "ActressRankingPage", **variables: Any) -> Any:
        payload = {
            "operationName": operation,
            "variables": {
                "filter": {"monthly": {"floor": "AV"}},
                "limit": 100,
                "offset": 0,
                **variables,
            },
        }
        return SimpleNamespace(
            url=GRAPHQL_URL,
            request=SimpleNamespace(method="POST", post_data=json.dumps(payload)),
        )

    spider = FanzaActressRankingSpider()
    assert spider.is_ranking_response(response())
    assert not spider.is_ranking_response(response(operation="SideBar"))
    assert not spider.is_ranking_response(response(limit=5))
    assert not spider.is_ranking_response(response(offset=1))
    assert not spider.is_ranking_response(
        response(filter={"monthly": {"floor": "DVD"}})
    )

    wrong_method = response()
    wrong_method.request.method = "GET"
    assert not spider.is_ranking_response(wrong_method)
    wrong_url = response()
    wrong_url.url = "https://example.test/graphql"
    assert not spider.is_ranking_response(wrong_url)


class FakeResponseInfo(AbstractContextManager):
    def __init__(self, response: Any, events: list[str]) -> None:
        self.value = response
        self.events = events

    def __enter__(self) -> FakeResponseInfo:
        self.events.append("expect")
        return self

    def __exit__(self, *args: object) -> None:
        return None


class FakePage:
    def __init__(self, events: list[str], response: Any) -> None:
        self.events = events
        self.response = response
        self.url = spider_module.URL

    def expect_response(self, predicate: Any, timeout: int) -> FakeResponseInfo:
        assert predicate(self.response)
        return FakeResponseInfo(self.response, self.events)

    def goto(self, url: str, **kwargs: object) -> Any:
        self.events.append("goto")
        return SimpleNamespace(status=200)


class FakeBrowser:
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def new_context(self, **kwargs: object) -> Any:
        return SimpleNamespace(
            add_cookies=lambda cookies: None,
            new_page=lambda: FakePage(self.events, ranking_response),
        )

    def close(self) -> None:
        self.events.append("close")


class FakePlaywright:
    def __init__(self, events: list[str], launch_args: dict) -> None:
        self.chromium = SimpleNamespace(
            launch=lambda **kwargs: launch_args.update(kwargs) or FakeBrowser(events)
        )


class FakePlaywrightContext(AbstractContextManager):
    def __init__(self, playwright: FakePlaywright) -> None:
        self.playwright = playwright

    def __enter__(self) -> FakePlaywright:
        return self.playwright

    def __exit__(self, *args: object) -> None:
        return None


ranking_response = SimpleNamespace(
    url=GRAPHQL_URL,
    status=200,
    request=SimpleNamespace(
        method="POST",
        post_data=json.dumps(
            {
                "operationName": "ActressRankingPage",
                "variables": {
                    "filter": {"monthly": {"floor": "AV"}},
                    "limit": 100,
                    "offset": 0,
                },
            }
        ),
    ),
    json=lambda: {"data": {"ppvActressRanking": {"items": ranking_items(1)}}},
)


def test_fetch_waits_for_exact_response_and_closes_browser() -> None:
    events: list[str] = []
    launch_args: dict = {}
    factory = lambda: FakePlaywrightContext(  # noqa: E731
        FakePlaywright(events, launch_args)
    )
    spider = FanzaActressRankingSpider(playwright_factory=factory)

    parsed = spider.fetch_ranking(1)

    assert [item["rank"] for item in parsed] == [1]
    assert events == ["expect", "goto", "close"]
    assert launch_args["proxy"] is None


def test_default_output_mirrors_identical_files_and_uses_utc(
    tmp_path: Path, monkeypatch
) -> None:
    default = tmp_path / "docs" / "zh" / "排名"
    monkeypatch.setattr(spider_module, "DEFAULT_OUTPUT_DIR", default)
    spider = FanzaActressRankingSpider(output_dir=str(default))
    now = datetime(2026, 8, 1, 1, 0, tzinfo=timezone(timedelta(hours=9)))

    destination = spider.save_yaml(spider.parse_items(ranking_items(1), 1), now=now)

    assert destination == default / "actress-ranking-202607.yaml"
    paths = [
        destination,
        tmp_path / "docs" / "ja" / "排名" / destination.name,
        tmp_path / "docs" / "en" / "排名" / destination.name,
    ]
    assert all(path.is_file() for path in paths)
    assert len({path.read_bytes() for path in paths}) == 1
    payload = yaml.safe_load(destination.read_text(encoding="utf-8"))
    assert payload["fetched_at"] == "2026-07-31T16:00:00Z"
    assert payload["count"] == 1


def test_custom_output_does_not_touch_repository(tmp_path: Path) -> None:
    output = tmp_path / "custom"
    spider = FanzaActressRankingSpider(output_dir=str(output))

    destination = spider.save_yaml(
        spider.parse_items(ranking_items(1), 1),
        now=datetime(2026, 7, 1, tzinfo=UTC),
    )

    assert destination.parent == output
    assert list(output.iterdir()) == [destination]


def test_source_file_is_not_replaced_when_mirror_fails(
    tmp_path: Path, monkeypatch
) -> None:
    default = tmp_path / "docs" / "zh" / "排名"
    monkeypatch.setattr(spider_module, "DEFAULT_OUTPUT_DIR", default)
    spider = FanzaActressRankingSpider(output_dir=str(default))
    destination = default / "actress-ranking-202607.yaml"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"old source\n")
    real_replace = os.replace
    calls = 0

    def fail_second_replace(source: str, target: str) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated mirror failure")
        real_replace(source, target)

    monkeypatch.setattr(spider_module.os, "replace", fail_second_replace)

    with pytest.raises(OSError, match="simulated"):
        spider.save_yaml(
            spider.parse_items(ranking_items(1), 1),
            now=datetime(2026, 7, 1, tzinfo=UTC),
        )

    assert destination.read_bytes() == b"old source\n"
    assert not list(default.glob(".actress-ranking-202607.yaml.*"))


def test_cli_rejects_invalid_limit_before_running(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        spider_module.main(["--limit", "0", "--output", str(tmp_path)])

    assert exc.value.code == 2


def test_cli_reports_fetch_errors(monkeypatch, tmp_path: Path, capsys) -> None:
    def fail(self: FanzaActressRankingSpider, limit: int) -> list[dict]:
        raise RuntimeError("network failed")

    monkeypatch.setattr(FanzaActressRankingSpider, "run", fail)
    result = spider_module.main(["--limit", "1", "--output", str(tmp_path)])

    assert result == 1
    assert "network failed" in capsys.readouterr().err
