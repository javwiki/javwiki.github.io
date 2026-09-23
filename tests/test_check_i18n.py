from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from scripts import check_i18n as checker


def ranking_payload() -> dict:
    return {
        "source": "FANZA",
        "type": "actress_monthly_ranking",
        "url": "https://example.test/ranking",
        "fetched_at": "2026-07-04T22:41:33+00:00",
        "count": 2,
        "rankings": [
            {
                "rank": 1,
                "actress_id": "100",
                "name": "First",
                "image": "https://example.test/1.jpg",
                "contents_count": 10,
                "latest_content_id": "abc001",
                "latest_title": "Shared title",
            },
            {
                "rank": 2,
                "actress_id": "200",
                "name": "Second",
                "image": "https://example.test/2.jpg",
                "contents_count": 20,
                "latest_content_id": "abc001",
                "latest_title": "Shared title",
                "extension_field": "allowed",
            },
        ],
    }


def test_targets_are_in_document_order() -> None:
    text = '<img src="image.png">\n[entry](page.md)\n<https://example.test>\n'

    assert checker.targets(text) == [
        "image.png",
        "page.md",
        "https://example.test",
    ]


def test_compare_detects_cross_kind_link_reordering() -> None:
    source = '<img src="image.png">\n[entry](page.md)\n<https://example.test>\n'
    translated = '<https://example.test>\n<img src="image.png">\n[entry](page.md)\n'

    assert "link targets" in checker.compare(source, translated)


def test_fence_languages_reads_opening_markers_only() -> None:
    text = "```python\npass\n```\n~~~text\nplain\n~~~\n````\nbody\n````\n"

    assert checker.fence_languages(text) == ["python", "text", ""]


def test_compare_detects_fence_language_drift() -> None:
    source = "```python\nprint('ok')\n```\n"
    translated = "```javascript\nconsole.log('ok')\n```\n"

    assert "code fence languages" in checker.compare(source, translated)


def test_ranking_schema_accepts_duplicate_latest_content_and_extensions() -> None:
    assert checker.ranking_problems(ranking_payload()) == []


def test_ranking_schema_rejects_count_mismatch() -> None:
    data = ranking_payload()
    data["count"] = 1

    assert any("count" in problem for problem in checker.ranking_problems(data))


def test_ranking_schema_rejects_non_integer_count() -> None:
    data = ranking_payload()
    data["count"] = True

    assert any("count" in problem for problem in checker.ranking_problems(data))


def test_ranking_schema_rejects_rank_gaps_and_reordering() -> None:
    data = ranking_payload()
    data["rankings"][1]["rank"] = 3
    assert any("ordered ranks" in problem for problem in checker.ranking_problems(data))

    data = ranking_payload()
    data["rankings"][0]["rank"], data["rankings"][1]["rank"] = 2, 1
    assert any("ordered ranks" in problem for problem in checker.ranking_problems(data))


def test_ranking_schema_rejects_duplicate_actress_id() -> None:
    data = ranking_payload()
    data["rankings"][1]["actress_id"] = data["rankings"][0]["actress_id"]

    assert any(
        "duplicate actress_id" in problem for problem in checker.ranking_problems(data)
    )


def test_ranking_schema_rejects_missing_item_fields() -> None:
    data = ranking_payload()
    del data["rankings"][0]["image"]

    assert any("missing image" in problem for problem in checker.ranking_problems(data))


def test_list_schema_rejects_wrong_field_types() -> None:
    data = {
        "title": "Actresses",
        "items": [{"name": "A", "row": "あ", "col": 1, "completeness": "100%"}],
    }

    assert any(
        "invalid `col`" in problem for problem in checker.list_schema_problems(data)
    )


def test_markdown_list_names_preserves_source_order() -> None:
    text = "# List\n\n## あ\n\n- First\n- Second\n\n```text\n- ignored\n```\n"

    assert checker.markdown_list_names(text) == ["First", "Second"]


def make_list_tree(root: Path) -> tuple[list[dict], list[dict]]:
    source_items = [
        {"name": "天海翼", "row": "あ", "col": "あ", "completeness": "100%"},
        {"name": "AIKA", "row": "あ", "col": "あ", "completeness": "80%"},
    ]
    target_items = [
        {"name": "天海つばさ", "row": "あ", "col": "あ", "completeness": "100%"},
        {"name": "アイカ", "row": "あ", "col": "あ", "completeness": "80%"},
    ]
    for language in checker.LANGUAGES:
        base = root / language
        for item in source_items:
            path = base / item["row"] / item["col"] / f"{item['name']}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# entry\n", encoding="utf-8")
    return source_items, target_items


def test_list_mapping_allows_translated_display_names(tmp_path: Path) -> None:
    source_items, target_items = make_list_tree(tmp_path)
    for items in (source_items, target_items):
        list_text = "\n".join(f"- {item['name']}" for item in items)
        assert (
            checker.list_mapping_problems(
                "zh" if items is source_items else "ja",
                items,
                list_text,
                source_items,
                tmp_path,
            )
            == []
        )


def test_list_mapping_reports_missing_page(tmp_path: Path) -> None:
    source_items, target_items = make_list_tree(tmp_path)
    (tmp_path / "ja" / "あ" / "あ" / "天海翼.md").unlink()
    list_text = "\n".join(f"- {item['name']}" for item in target_items)

    problems = checker.list_mapping_problems(
        "ja", target_items, list_text, source_items, tmp_path
    )

    assert any("list.yaml page not found" in problem for problem in problems)


def test_list_mapping_reports_markdown_and_metadata_drift(tmp_path: Path) -> None:
    source_items = [
        {"name": "天海翼", "row": "あ", "col": "あ", "completeness": "100%"}
    ]
    target_items = deepcopy(source_items)
    target_items[0]["completeness"] = "80%"
    path = tmp_path / "ja" / "あ" / "あ" / "天海翼.md"
    path.parent.mkdir(parents=True)
    path.write_text("# entry\n", encoding="utf-8")

    problems = checker.list_mapping_problems(
        "ja", target_items, "- Wrong name\n", source_items, tmp_path
    )

    assert any("list.md differs" in problem for problem in problems)
    assert any("completeness" in problem for problem in problems)


def test_active_html_is_rejected_but_code_examples_are_allowed() -> None:
    relative = Path("page.md")
    assert checker.unsafe_html_problems(relative, '<img onerror="x">') != []
    assert checker.unsafe_html_problems(relative, "<p>safe</p>") == []
    assert (
        checker.unsafe_html_problems(
            relative, "```html\n<script>alert(1)</script>\n```\n"
        )
        == []
    )


def test_repository_satisfies_extended_data_contracts() -> None:
    assert checker.yaml_problems() == []
