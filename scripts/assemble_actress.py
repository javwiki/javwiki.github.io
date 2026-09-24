#!/usr/bin/env python3
"""Assemble translated actress pages into full i18n-conforming files.

Actress pages start with YAML front matter and (usually) a large ``<img>``
line — both are data that must stay byte-identical to the Chinese source, and
retyping them invites drift. Translations are therefore written body-only:

    # Arina Arata

    %%IMG%%

    ## Basic information
    ...

This script wraps the body: it prepends the Chinese front matter, replaces
``%%IMG%%`` with the Chinese ``<img>`` line (with ``alt`` set to the English
display name), then runs the structural comparison of ``check_i18n`` and
reports any mismatch.

Run from the repository root:

    python3 scripts/assemble_actress.py           # assemble pending pages
    python3 scripts/assemble_actress.py --check   # report only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_i18n  # noqa: E402
from en_display_names import english_names  # noqa: E402

ZH = check_i18n.ROOT / "zh"
EN = check_i18n.ROOT / "en"

IMG_LINE = re.compile(r'^<img\b[^>]*>\s*$', re.M)
ALT = re.compile(r'(<img\b[^>]*?\balt=")([^"]+)(")')


def pending() -> list[Path]:
    """English actress pages still written without front matter."""
    out = []
    for zh_path in sorted(ZH.glob("*/*/*.md")):
        if zh_path.name == "index.md":
            continue
        en_path = EN / zh_path.relative_to(ZH)
        text = en_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            out.append(en_path)
    return out


def assemble(zh_path: Path, en_text: str, names: dict[str, str]) -> str:
    zh_text = zh_path.read_text(encoding="utf-8")
    match = check_i18n.FRONT_MATTER.match(zh_text)
    front = match.group(0) if match else ""
    body = zh_text[len(front) :]

    img_match = IMG_LINE.search(body)
    img = ""
    if img_match:
        img = img_match.group(0)
        name = names.get(zh_path.stem)
        if name:
            img = ALT.sub(lambda m: m.group(1) + name + m.group(3), img, count=1)

    if "%%IMG%%" in en_text:
        if img:
            en_text = en_text.replace("%%IMG%%", img, 1)
        else:
            en_text = re.sub(r"%%IMG%%\n+", "", en_text, count=1)
    elif img:
        # No placeholder: insert right after the H1, as in the Chinese source.
        head, sep, rest = en_text.partition("\n")
        en_text = f"{head}{sep}\n{img}\n{rest.lstrip(chr(10))}"
        print(f"  note: {zh_path.name}: inserted <img> after H1 (no %%IMG%%)")

    return front + en_text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    names = english_names()
    errors: list[str] = []
    done = 0
    for en_path in pending():
        relative = en_path.relative_to(EN)
        zh_path = ZH / relative
        assembled = assemble(zh_path, en_path.read_text(encoding="utf-8"), names)
        zh_text = zh_path.read_text(encoding="utf-8")
        problems = check_i18n.compare(zh_text, assembled)
        problems += check_i18n.unprotected_problems("en", relative, assembled)
        label = f"docs/en/{relative}"
        if problems:
            errors.append(f"{label}: {', '.join(problems)}")
        if not args.check:
            en_path.write_text(assembled, encoding="utf-8")
        done += 1
        print(f"{'would assemble' if args.check else 'assembled'} {label}")

    print(f"{done} files, {len(errors)} with structural problems")
    for error in errors:
        print(f"  {error}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
