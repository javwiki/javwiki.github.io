#!/usr/bin/env python3
"""Fail when the Chinese, Japanese, and English content trees drift apart."""

from pathlib import Path


LANGUAGES = ("zh", "ja", "en")


def files(language: str) -> set[Path]:
    root = Path("docs") / language
    return {path.relative_to(root) for path in root.rglob("*") if path.is_file()}


trees = {language: files(language) for language in LANGUAGES}
all_files = set().union(*trees.values())
has_errors = False

for language in LANGUAGES:
    missing = sorted(all_files - trees[language])
    if missing:
        has_errors = True
        print(f"Missing from docs/{language}:")
        print(*(f"  {path}" for path in missing), sep="\n")

if has_errors:
    raise SystemExit(1)

print(f"i18n trees match ({len(all_files)} files per language)")
