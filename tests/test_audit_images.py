from pathlib import Path

import pytest

from scripts.checks.audit_images import image_references, inventory


def test_all_reference_types_without_claiming_visual_verification(
    tmp_path: Path,
) -> None:
    body = """---
thumbnail: https://example.test/portrait.jpg
---
<img src='https://example.test/portrait.jpg' alt="Person" />
![Portrait](https://example.test/other.png)
![Archive][photo]
[photo]: https://example.test/archive.jpg
```html
<img src="https://example.test/example-only.jpg">
```
"""
    for language in ("zh", "ja", "en"):
        base = tmp_path / "docs" / language / "人物" / "女优" / "あ" / "あ"
        base.mkdir(parents=True)
        (base / "Person.md").write_text(body)
        (base / "Missing.md").write_text("# No image\n")
    report = inventory(tmp_path)
    assert report["unique_images"] == 3
    assert report["counts"]["zh"] == {"markdown_pages_scanned": 2, "references": 4}
    assert len(report["pages"]) == 6
    assert report["translation_drift"] == []
    assert {p["review_status"] for p in report["pages"]} == {
        "not_reviewed",
        "not_applicable",
    }
    assert all(p["issues"] == [] for p in report["pages"])
    translated = tmp_path / "docs" / "en" / "人物" / "女优" / "あ" / "あ" / "Person.md"
    translated.write_text(body.replace("other.png", "wrong.png"))
    assert inventory(tmp_path)["translation_drift"] == [
        {"page": "人物/女优/あ/あ/Person.md", "language": "en"}
    ]


def test_empty_old_content_root_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    with pytest.raises(ValueError, match="refusing an empty audit"):
        inventory(tmp_path)


def test_html_sources_and_missing_alt_are_retained() -> None:
    refs = image_references(
        '<picture><source srcset="a.webp 1x, b.webp 2x"><img src="a.jpg"></picture>'
    )
    assert [r["url"] for r in refs] == ["a.webp", "b.webp", "a.jpg"]
    assert refs[-1]["alt"] == ""


def test_missing_alt_and_thumbnail_disagreement(tmp_path: Path) -> None:
    body = "---\nthumbnail: wrong.jpg\n---\n<img src='portrait.jpg'>\n"
    for language in ("zh", "ja", "en"):
        page = tmp_path / "docs" / language / "page.md"
        page.parent.mkdir(parents=True)
        page.write_text(body)
    assert inventory(tmp_path)["pages"][0]["issues"] == [
        "thumbnail_display_mismatch",
        "missing_alt",
    ]


def test_metadata_only_thumbnail_is_not_a_display_mismatch(tmp_path: Path) -> None:
    for language in ("zh", "ja", "en"):
        page = tmp_path / "docs" / language / "work.md"
        page.parent.mkdir(parents=True)
        page.write_text("---\nthumbnail: cover.jpg\n---\n# Work\n")
    assert inventory(tmp_path)["pages"][0]["issues"] == ["thumbnail_metadata_only"]
