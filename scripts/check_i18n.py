#!/usr/bin/env python3
"""Guard the trilingual content trees against drift.

Chinese (`docs/zh/`) is the source of truth. The Japanese and English
editions are translations of it and must stay structurally identical to it:
same file set, same front matter, same heading hierarchy, same link targets,
same table shape, same code fences. Only prose is translated.

Run directly or via `./scripts/build_site.sh`, which runs it before building.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SOURCE = "zh"
TARGETS = ("ja", "en")
ROOT = Path(__file__).resolve().parent.parent / "docs"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
HEADING = re.compile(r"^(#{1,6})[ \t]", re.M)
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
AUTOLINK = re.compile(r"<((?:https?|mailto):[^>\s]+)>")
IMG_SRC = re.compile(r"<img\b[^>]*?\bsrc=\"([^\"]+)\"")
FENCE = re.compile(r"^(?:```+|~~~+)", re.M)

# `title` is the page/nav label shown to readers, so each edition translates it.
# Everything else in the front matter is data and stays byte-identical.
TRANSLATABLE_FRONT_MATTER = ("title",)


def front_matter(text: str) -> str:
    match = FRONT_MATTER.match(text)
    if not match:
        return ""
    kept = [
        line
        for line in match.group(1).split("\n")
        if line.split(":", 1)[0] not in TRANSLATABLE_FRONT_MATTER
    ]
    return "\n".join(kept)


def heading_levels(text: str) -> list[int]:
    return [len(match.group(1)) for match in HEADING.finditer(text)]


def targets(text: str) -> list[str]:
    """Link targets, autolinks and image sources, in document order."""
    return LINK.findall(text) + AUTOLINK.findall(text) + IMG_SRC.findall(text)


def table_shape(text: str) -> list[int]:
    """Pipe count of every table line, code fences excluded."""
    shape: list[int] = []
    fenced = False
    for line in text.split("\n"):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced and line.startswith("|"):
            shape.append(line.count("|"))
    return shape


def compare(source: str, translated: str) -> list[str]:
    problems = []
    if front_matter(source) != front_matter(translated):
        problems.append("front matter")
    if heading_levels(source) != heading_levels(translated):
        problems.append("heading levels")
    if targets(source) != targets(translated):
        problems.append("link targets")
    if table_shape(source) != table_shape(translated):
        problems.append("table shape")
    if len(FENCE.findall(source)) != len(FENCE.findall(translated)):
        problems.append("code fences")
    return problems


def missing_files(trees: dict[str, set[Path]], language: str) -> list[Path]:
    everywhere = set().union(*trees.values())
    return sorted(everywhere - trees[language])


def main() -> int:
    trees = {
        language: {
            path.relative_to(ROOT / language)
            for path in (ROOT / language).rglob("*")
            if path.is_file()
        }
        for language in (SOURCE, *TARGETS)
    }

    errors: list[str] = []
    for language in (SOURCE, *TARGETS):
        for path in missing_files(trees, language):
            errors.append(f"Missing from docs/{language}: {path}")

    checked = 0
    for language in TARGETS:
        for relative in sorted(trees[language]):
            if relative.suffix != ".md":
                continue
            source_path = ROOT / SOURCE / relative
            translated_path = ROOT / language / relative
            if not source_path.is_file():
                continue
            checked += 1
            problems = compare(
                source_path.read_text(encoding="utf-8"),
                translated_path.read_text(encoding="utf-8"),
            )
            if problems:
                errors.append(f"docs/{language}/{relative}: {', '.join(problems)}")

    if errors:
        print("i18n check failed:", file=sys.stderr)
        print(*(f"  {error}" for error in errors), sep="\n", file=sys.stderr)
        return 1

    count = len(trees[SOURCE])
    print(f"i18n trees match ({count} files per language, {checked} pages structurally checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
