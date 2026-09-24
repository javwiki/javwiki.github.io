#!/usr/bin/env python3
"""Apply English display names across ``docs/en``.

The Chinese source is the origin of truth for every performer's English name
(``- **英文名**: Arina Arata``). This script derives the mapping from it and
re-applies it to the English tree so that H1s, ``alt`` attributes, link display
text and ``_meta/list.{md,yaml}`` agree with each other, no matter which pass
touched the page last.

Only display text changes: link targets, heading levels, table shapes, code
fences and front matter are untouched, so ``check_i18n.py`` stays green.

Run from the repository root:

    python3 scripts/en_display_names.py           # apply
    python3 scripts/en_display_names.py --check   # report drift only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
ZH = ROOT / "docs" / "zh"
EN = ROOT / "docs" / "en"

# Chinese-source pages without an `英文名` field: English name taken from the
# kana reading those pages carry (given name first, matching the field's
# convention, e.g. 新有菜 -> Arina Arata).
OVERRIDES: dict[str, str] = {
    "一条みお": "Mio Ichijou",
    "おりん": "Orin",
    "城星凜": "Seri Kizuki",
    "橘芹那": "Serina Tachibana",
    "鷹宮ゆい": "Yui Takanomiya",
    "九十九メイ": "Mei Tsukumo",
    "天馬ゆい": "Yui Tenma",
    "桥本有菜": "Arina Hashimoto",
    "姫川ゆうな": "Yuuna Himekawa",
}

# H1s whose Chinese source carries an annotation in addition to the name.
H1_OVERRIDES: dict[str, str] = {
    "桥本有菜": "Arina Hashimoto (now: Arina Arata)",
}

FIELD = re.compile(r"^- \*\*英文名\*\*[:：]\s*(.*)$", re.M)
FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
FENCE = re.compile(r"^(?:```+|~~~+)")
LINK = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
IMG_ALT = re.compile(r'(<img\b[^>]*?\balt=")([^"]+)(")')
NEXT_HEADING = re.compile(r"^#{1,6}[ \t]")

# Protected sections (official Japanese / Chinese对照) must stay byte-identical
# to the Chinese source; never rewrite their display text.
PROTECTED = re.compile(
    r"^### (?:日文原文（missAV / FANZA）|日文原文"
    r"|Original Japanese \(missAV / FANZA\)|Original Japanese"
    r"|中文翻译|中国語訳|Chinese translation)[ \t]*$"
)


def english_names() -> dict[str, str]:
    """Chinese file stem -> English display name."""
    names: dict[str, str] = {}
    missing: list[str] = []
    for page in sorted(ZH.glob("*/*/*.md")):
        if page.name == "index.md":
            continue
        text = page.read_text(encoding="utf-8")
        match = FIELD.search(text)
        if match and match.group(1).strip():
            # Field may offer alternatives: keep the primary spelling.
            names[page.stem] = match.group(1).strip().split(" / ")[0].strip()
        elif page.stem in OVERRIDES:
            names[page.stem] = OVERRIDES[page.stem]
        else:
            missing.append(page.stem)
    if missing:
        raise SystemExit(
            "no English name and no override for: " + ", ".join(sorted(missing))
        )
    return names


def rewrite_links(text: str, names: dict[str, str]) -> tuple[str, int]:
    """Replace display text of links to mapped performer pages, line by line.

    Fenced code blocks and protected sections are passed through untouched.
    """
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        target = match.group(2)
        if target.startswith(("http://", "https://", "mailto:", "#")):
            return match.group(0)
        name = names.get(Path(unquote(target.split("#", 1)[0])).stem)
        if name is None or name == match.group(1):
            return match.group(0)
        count += 1
        return f"[{name}]({target})"

    out: list[str] = []
    fence: str | None = None
    protected = False
    for line in text.split("\n"):
        marker = FENCE.match(line)
        if marker:
            fence = None if fence and line.startswith(fence) else (fence or marker.group(0))
            out.append(line)
            continue
        if fence:
            out.append(line)
            continue
        if PROTECTED.match(line):
            protected = True
            out.append(line)
            continue
        if protected and NEXT_HEADING.match(line):
            protected = False
        out.append(line if protected else replace_line(line, replace))
    return "\n".join(out), count


def replace_line(line: str, replace) -> str:
    return LINK.sub(replace, line) if "[" in line else line


def page_updates(
    relative: Path, text: str, names: dict[str, str]
) -> tuple[str, list[str]]:
    """H1, alt attribute, link display and list files for one English page."""
    notes: list[str] = []
    is_actress = len(relative.parts) == 3 and relative.name != "index.md"
    if is_actress and relative.stem in names:
        name = names[relative.stem]
        h1 = H1_OVERRIDES.get(relative.stem, name)
        prefix_len = len(FRONT_MATTER.match(text).group(0)) if FRONT_MATTER.match(text) else 0
        body = text[prefix_len:]
        head, sep, rest = body.partition("\n")
        if head.startswith("# ") and head != f"# {h1}":
            notes.append(f"H1: {head[2:]} -> {h1}")
            body = f"# {h1}{sep}{rest}"
            text = text[:prefix_len] + body
        alt_target = relative.stem

        def alt(match: re.Match[str]) -> str:
            if match.group(2) != alt_target:
                return match.group(0)
            notes.append(f"alt -> {name}")
            return f"{match.group(1)}{name}{match.group(3)}"

        text = IMG_ALT.sub(alt, text)

    text, links = rewrite_links(text, names)
    if links:
        notes.append(f"{links} link display(s)")

    if relative == Path("_meta/list.yaml"):
        text, changed = rename_list(text, r"^(\s*- name: )(.+)$", names)
        if changed:
            notes.append(f"{changed} list.yaml names")
    elif relative == Path("_meta/list.md"):
        text, changed = rename_list(text, r"^(- )(.+?)\s*$", names, whole=True)
        if changed:
            notes.append(f"{changed} list.md names")
    return text, notes


def rename_list(
    text: str, pattern: str, names: dict[str, str], whole: bool = False
) -> tuple[str, int]:
    """Rewrite performer names in `_meta/list.{yaml,md}` bullet lines."""
    regex = re.compile(pattern)
    changed = 0
    out = []
    for line in text.split("\n"):
        match = regex.match(line)
        if match and match.group(2).strip() in names:
            new = names[match.group(2).strip()]
            if new != match.group(2):
                line = f"{match.group(1)}{new}"
                changed += 1
        out.append(line)
    return "\n".join(out), changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report only")
    args = parser.parse_args()

    names = english_names()
    changed_files = 0
    # `_meta/list.yaml` carries the same display names as `list.md`; the
    # ranking YAMLs are byte-identical data mirrors and are never touched.
    pages = sorted(EN.rglob("*.md")) + [EN / "_meta" / "list.yaml"]
    for page in pages:
        if not page.is_file():
            continue
        relative = page.relative_to(EN)
        original = page.read_text(encoding="utf-8")
        updated, notes = page_updates(relative, original, names)
        if updated == original:
            continue
        changed_files += 1
        if args.check:
            print(f"drift: docs/en/{relative}: {', '.join(notes)}")
        else:
            page.write_text(updated, encoding="utf-8")
            print(f"docs/en/{relative}: {', '.join(notes)}")
    verb = "would change" if args.check else "changed"
    print(f"{verb} {changed_files} files ({len(names)} mapped names)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
