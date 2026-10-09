#!/usr/bin/env python3
"""Apply the English display name to sentence openings in `docs/en`.

maintenance/TRANSLATION.md fixes the English display name per edition, and the Japanese
edition already opens with its own standard name. This rewrites the leading
Chinese file-name form of an English sentence or list item to the page's own
H1, which is the authoritative display name, and touches nothing else.

Run with --check to report only.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EN = ROOT / "docs" / "en"
FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
FENCE = re.compile(r"^(?:```+|~~~+)")
H1 = re.compile(r"^#\s+(.+)$", re.M)
PROTECTED = re.compile(
    r"^### (?:日文原文（missAV / FANZA）|日文原文"
    r"|Original Japanese \(missAV / FANZA\)|Original Japanese"
    r"|中文翻译|中国語訳|Chinese translation)[ \t]*$",
    re.M,
)
NEXT_HEADING = re.compile(r"^#{1,6}[ \t]")
# Spans whose original spelling is intentional: official titles, stage names in
# brackets, parenthesised glosses and URLs.
KEEP = re.compile(
    r"「[^」]*」|『[^』]*』|《[^》]*》|\([^)]*\)|（[^）]*）|https?://\S+|\"[^\"]*\""
)
OPENING = re.compile(
    r"^(?P<head>\s*(?:[-*+]\s+)?)(?P<name>[^\s]+?)(?P<rest>\s+(?:is|was|are|were)\b)"
)
LATIN = re.compile(r"[A-Za-z]")


def rewrite(text: str, stem: str, display: str) -> tuple[str, int]:
    out: list[str] = []
    fence: str | None = None
    protected = False
    count = 0
    for line in text.split("\n"):
        marker = FENCE.match(line)
        if marker:
            fence = (
                None
                if fence and marker.group(0).startswith(fence)
                else (fence or marker.group(0))
            )
            out.append(line)
            continue
        if fence or protected:
            out.append(line)
            if not fence and NEXT_HEADING.match(line):
                protected = False
            continue
        match = OPENING.match(KEEP.sub(" ", line))
        if match and match.group("name") == stem and stem != display:
            start = line.index(stem, len(match.group("head")))
            line = line[:start] + display + line[start + len(stem) :]
            count += 1
        out.append(line)
    return "\n".join(out), count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = 0
    total = 0
    for page in sorted(EN.glob("人物/女优/*/*/*.md")):
        if page.name == "index.md":
            continue
        text = page.read_text(encoding="utf-8")
        head = H1.search(FRONT_MATTER.sub("", text))
        if not head:
            print(f"!! no H1: {page}")
            continue
        display = head.group(1).strip()
        if display == page.stem:
            continue  # the stage name is the file name; nothing to rename
        # An H1 may keep a Japanese annotation (`An Mitsumi (藤井蘭々)`); what it
        # must never be is a heading without a Latin display name.
        if not LATIN.search(display):
            print(f"!! unusable H1: {page.relative_to(EN)} -> {display}")
            continue
        new, count = rewrite(text, page.stem, display)
        if not count:
            continue
        total += count
        changed += 1
        if args.check:
            print(f"would change {count} line(s) in {page.relative_to(EN)}")
        else:
            page.write_text(new, encoding="utf-8")
    print(
        f"{'would update' if args.check else 'updated'} {total} line(s) in {changed} page(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
