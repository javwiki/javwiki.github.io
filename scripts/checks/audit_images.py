#!/usr/bin/env python3
"""Inventory image references in the current trilingual content trees.

This is an offline coverage check, not a visual or identity verdict. Remote
availability, visual review and source attribution must be recorded separately.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import yaml

LANGUAGES = ("zh", "ja", "en")
ROOT = Path(__file__).resolve().parents[2]


class ImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.images: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "img" and values.get("src"):
            self.images.append(
                {"kind": "html", "url": values["src"], "alt": values.get("alt") or ""}
            )
        if tag in {"img", "source"} and values.get("srcset"):
            for item in values["srcset"].split(","):
                url = item.strip().split()[0] if item.strip() else ""
                if url:
                    self.images.append({"kind": "srcset", "url": url, "alt": ""})


def image_references(content: str) -> list[dict[str, str]]:
    references: list[dict[str, str]] = []
    if content.startswith("---\n"):
        _, front, content = content.split("---", 2)
        metadata = yaml.safe_load(front) or {}
        thumbnail = metadata.get("thumbnail")
        if thumbnail:
            references.append({"kind": "thumbnail", "url": str(thumbnail), "alt": ""})
    # Example code is not a rendered image.
    content = re.sub(r"(?ms)^(`{3,}|~{3,}).*?^\1[^\n]*$", "", content)
    content = re.sub(r"`[^`\n]+`", "", content)
    parser = ImageParser()
    parser.feed(content)
    references.extend(parser.images)
    for match in re.finditer(
        r'!\[([^\]]*)\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+["\x27][^\n]*?)?\s*\)', content
    ):
        references.append(
            {
                "kind": "markdown",
                "url": html.unescape(match[2].strip("<>")),
                "alt": match[1],
            }
        )
    definitions = {
        match[1].casefold(): match[2].strip("<>")
        for match in re.finditer(r"(?m)^\s*\[([^\]]+)\]:\s*(<[^>]+>|\S+)", content)
    }
    for match in re.finditer(r"!\[([^\]]*)\]\[([^\]]*)\]", content):
        key = (match[2] or match[1]).casefold()
        if key in definitions:
            references.append(
                {"kind": "markdown_reference", "url": definitions[key], "alt": match[1]}
            )
    return references


def inventory(root: Path) -> dict:
    pages = []
    counts: dict[str, dict[str, int]] = {}
    for language in LANGUAGES:
        base = root / "docs" / language
        files = sorted(base.rglob("*.md"))
        if not files:
            raise ValueError(
                f"No Markdown content found in {base}; refusing an empty audit"
            )
        references = 0
        for path in files:
            refs = image_references(path.read_text(encoding="utf-8"))
            relative = path.relative_to(base).as_posix()
            actress = relative.startswith("人物/女优/") and path.name != "index.md"
            if not refs and not actress:
                continue
            thumbnails = {r["url"] for r in refs if r["kind"] == "thumbnail"}
            displayed = {r["url"] for r in refs if r["kind"] != "thumbnail"}
            issues = []
            if thumbnails and displayed and not thumbnails.issubset(displayed):
                issues.append("thumbnail_display_mismatch")
            if thumbnails and not displayed:
                issues.append("thumbnail_metadata_only")
            if any(
                not r["alt"]
                for r in refs
                if r["kind"] in {"html", "markdown", "markdown_reference"}
            ):
                issues.append("missing_alt")
            pages.append(
                {
                    "language": language,
                    "page": path.relative_to(root).as_posix(),
                    "relative_page": relative,
                    "references": refs,
                    "coverage": "has_image" if refs else "no_image",
                    "review_status": "not_reviewed" if refs else "not_applicable",
                    "issues": issues,
                }
            )
            references += len(refs)
        counts[language] = {
            "markdown_pages_scanned": len(files),
            "references": references,
        }
    drift = []
    by_page = {(p["language"], p["relative_page"]): p for p in pages}
    for page in pages:
        if page["language"] != "zh":
            continue
        expected = Counter((r["kind"], r["url"]) for r in page["references"])
        for language in LANGUAGES[1:]:
            target = by_page.get((language, page["relative_page"]))
            actual = (
                Counter((r["kind"], r["url"]) for r in target["references"])
                if target
                else None
            )
            if actual != expected:
                drift.append({"page": page["relative_page"], "language": language})
    # Also detect image references present only in a translation.
    for page in pages:
        if page["language"] != "zh" and ("zh", page["relative_page"]) not in by_page:
            drift.append({"page": page["relative_page"], "language": page["language"]})
    urls = {r["url"] for p in pages for r in p["references"]}
    domains = Counter(urlsplit(url).netloc or "local" for url in urls)
    return {
        "counts": counts,
        "unique_images": len(urls),
        "domains": dict(domains),
        "translation_drift": drift,
        "pages": pages,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, help="Write the full JSON inventory")
    args = parser.parse_args()
    try:
        report = inventory(args.root)
    except ValueError as error:
        parser.error(str(error))
    if args.output:
        args.output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    for language, counts in report["counts"].items():
        pages = [p for p in report["pages"] if p["language"] == language]
        missing = sum(p["coverage"] == "no_image" for p in pages)
        print(
            f"{language}: {counts['markdown_pages_scanned']} pages scanned, {counts['references']} image references, {missing} actress pages without images"
        )
    print(
        f"{report['unique_images']} distinct images; {len(report['translation_drift'])} translation differences"
    )
    for page in report["pages"]:
        if page["issues"]:
            print(f"{page['page']}: {', '.join(page['issues'])}")
    print(
        "Inventory only: image accessibility, visual content and source attribution are not verified."
    )
    return int(
        bool(
            report["translation_drift"]
            or any(
                issue in {"thumbnail_display_mismatch", "missing_alt"}
                for page in report["pages"]
                for issue in page["issues"]
            )
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
