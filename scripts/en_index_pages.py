#!/usr/bin/env python3
"""Rebuild the English gojūon index pages from the Chinese source.

The 47 row/column index pages (``docs/en/{row}/index.md`` and
``docs/en/{row}/{col}/index.md``) are formulaic: heading, one intro sentence,
a section heading and a link list. Only display names are localized. This
script regenerates them from ``docs/zh/`` so that they always list every entry
with the English display name, and rewrites the matching headings in
``docs/en/_meta/list.md``.

English display convention (see TRANSLATION.md):

- row page H1:    ``# A row (あ行)``
- column page H1: ``# A column (あ段) — A row (あ行)``
- headings are English first with the Japanese term in parentheses

Run from the repository root:

    python3 scripts/en_index_pages.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from en_display_names import english_names  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ZH = ROOT / "docs" / "zh"
EN = ROOT / "docs" / "en"

ROW_EN = {
    "あ": "A",
    "か": "Ka",
    "さ": "Sa",
    "た": "Ta",
    "な": "Na",
    "は": "Ha",
    "ま": "Ma",
    "や": "Ya",
    "ら": "Ra",
    "わ": "Wa",
}

SYLLABLES = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o",
    "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so",
    "た": "ta", "ち": "chi", "つ": "tsu", "て": "te", "と": "to",
    "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no",
    "は": "ha", "ひ": "hi", "ふ": "fu", "へ": "he", "ほ": "ho",
    "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo",
    "や": "ya", "ゆ": "yu", "よ": "yo",
    "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro",
    "わ": "wa", "を": "wo", "ん": "n",
    "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go",
    "ざ": "za", "じ": "ji", "ず": "zu", "ぜ": "ze", "ぞ": "zo",
    "だ": "da", "ぢ": "ji", "づ": "zu", "で": "de", "ど": "do",
    "ば": "ba", "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo",
    "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
}

LINK_LINE = re.compile(r"^- \[([^\]]*)\]\(([^)]+)\)\s*$")


def column_label(kana: str) -> str:
    return SYLLABLES[kana].capitalize() + " column"


def row_intro(row: str) -> str:
    if row == "は":
        return (
            "This row lists actresses whose stage name begins with a kana of the "
            "は row, including voiced 「ば・び・ぶ・べ・ぼ」 and semi-voiced "
            "「ぱ・ぴ・ぷ・ぺ・ぽ」."
        )
    return (
        f"This row lists actresses whose stage name begins with a kana of the "
        f"{row} row."
    )


def column_intro(kana: str, row: str) -> str:
    if kana in ("わ", "を", "ん"):
        return f"This column lists actresses whose stage name begins with {kana}."
    if kana == "べ":
        return (
            "This column lists actresses whose stage name begins with べ "
            "(classed as row ば, column え; included in the は row)."
        )
    return (
        f"This column lists actresses whose stage name begins with {kana} "
        f"(row {row}, column {kana})."
    )


def rebuild_row_index(relative: Path, zh_text: str) -> str:
    row = relative.parts[0]
    links = [line for line in zh_text.split("\n") if LINK_LINE.match(line)]
    return (
        f"# {ROW_EN[row]} row ({row}行)\n"
        f"\n{row_intro(row)}\n"
        f"\n## Column index\n\n"
        + "".join(f"{link}\n" for link in links)
    )


def rebuild_column_index(
    relative: Path, zh_text: str, names: dict[str, str]
) -> str:
    row, col = relative.parts[0], relative.parts[1]
    links = []
    missing = []
    for line in zh_text.split("\n"):
        match = LINK_LINE.match(line)
        if not match:
            continue
        stem = Path(match.group(2)).stem
        if stem not in names:
            missing.append(stem)
            continue
        links.append(f"- [{names[stem]}]({match.group(2)})")
    if missing:
        raise SystemExit(f"{relative}: no English name for {', '.join(missing)}")
    return (
        f"# {column_label(col)} ({col}段) — {ROW_EN[row]} row ({row}行)\n"
        f"\n{column_intro(col, row)}\n"
        f"\n## Entries\n\n"
        + "".join(f"{link}\n" for link in links)
    )


def relink_list_md(text: str) -> str:
    """Rewrite the H1 and row/column headings of `_meta/list.md`."""
    out = []
    for line in text.split("\n"):
        match = re.match(r"^## (.+?)行$", line)
        if match:
            row = match.group(1)
            line = f"## {ROW_EN[row]} row ({row}行)"
        else:
            match = re.match(r"^### (.+?)段$", line)
            if match:
                col = match.group(1)
                line = f"### {column_label(col)} ({col}段)"
            elif line.startswith("# "):
                line = "# AV actress list"
        out.append(line)
    return "\n".join(out)


def main() -> int:
    names = english_names()
    changed = 0
    for zh_path in sorted(ZH.rglob("index.md")):
        relative = zh_path.relative_to(ZH)
        if len(relative.parts) not in (2, 3):
            continue  # category/root indexes are translated by hand
        if relative.parts[0] not in ROW_EN:
            continue  # _meta/index.md and other non-gojūon indexes
        en_path = EN / relative
        zh_text = zh_path.read_text(encoding="utf-8")
        if len(relative.parts) == 2:
            new = rebuild_row_index(relative, zh_text)
        else:
            new = rebuild_column_index(relative, zh_text, names)
        old = en_path.read_text(encoding="utf-8") if en_path.is_file() else ""
        if new != old:
            en_path.parent.mkdir(parents=True, exist_ok=True)
            en_path.write_text(new, encoding="utf-8")
            changed += 1
            print(f"docs/en/{relative}")

    list_md = EN / "_meta" / "list.md"
    old = list_md.read_text(encoding="utf-8")
    new = relink_list_md(old)
    if new != old:
        list_md.write_text(new, encoding="utf-8")
        changed += 1
        print("docs/en/_meta/list.md (headings)")
    print(f"changed {changed} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
