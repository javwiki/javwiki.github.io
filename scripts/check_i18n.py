#!/usr/bin/env python3
"""Guard the trilingual content trees against drift.

Chinese (`docs/zh/`) is the source of the truth. The Japanese and English
editions are translations of it and must stay structurally identical to it:
same file set, same front matter, same heading hierarchy, same link targets,
same table shape, same code fences. Only prose is translated.

On top of the structural comparison it enforces data integrity that the
structural pass alone cannot see:

* link targets are complete (no bare-space truncation) and resolve to a file
* every `.md` in a segment directory is listed in that segment's `index.md`
* `_meta/list.yaml` and `排名/*.yaml` parse as YAML, agree on item count and
  carry no duplicate names
* `排名/*.yaml` stay byte-identical to the Chinese source
* the protected sections of `作品/` (official Japanese blurb and its Chinese
  translation) stay byte-identical to the Chinese source

Run directly (`uvx --with pyyaml python3 scripts/check_i18n.py`) or via
`./scripts/build_site.sh`, which runs it before building.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only on bare interpreters
    yaml = None

SOURCE = "zh"
TARGETS = ("ja", "en")
LANGUAGES = (SOURCE, *TARGETS)
ROOT = Path(__file__).resolve().parent.parent / "docs"

FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
HEADING = re.compile(r"^(#{1,6})[ \t]", re.M)
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
# Full target including whitespace, used to reject `(Some Page.md)` style links.
LINK_TARGET = re.compile(r"\]\(([^)]*)\)")
AUTOLINK = re.compile(r"<((?:https?|mailto):[^>\s]+)>")
IMG_SRC = re.compile(r"<img\b[^>]*?\bsrc=\"([^\"]+)\"")
FENCE = re.compile(r"^(?:```+|~~~+)", re.M)
SEGMENT_INDEX_ENTRY = re.compile(r"\]\(([^)#]+)")

# `title` is the page/nav label shown to readers, so each edition translates it.
# Everything else in the front matter is data and stays byte-identical.
TRANSLATABLE_FRONT_MATTER = ("title",)

# Sections that must be copied verbatim from the Chinese source, whatever the
# edition calls them. See TRANSLATION.md.
PROTECTED_SECTIONS = {
    "official blurb": (
        r"日文原文（missAV / FANZA）|日文原文"
        r"|Original Japanese \(missAV / FANZA\)|Original Japanese"
    ),
    "chinese translation": r"中文翻译|中国語訳|Chinese translation",
}


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


def section_body(text: str, pattern: str) -> str | None:
    """Body of a `### <pattern>` section, up to the next heading, verbatim."""
    match = re.search(rf"^### (?:{pattern})[ \t]*$", text, re.M)
    if not match:
        return None
    newline = text.find("\n", match.start())
    rest = text[newline + 1:] if newline >= 0 else ""
    stop = re.search(r"^#{1,6}[ \t]", rest, re.M)
    body = rest[: stop.start()] if stop else rest
    return body.rstrip("\n")


def bare_space_targets(text: str) -> list[str]:
    """Markdown targets containing whitespace, which `LINK` would truncate."""
    return [t for t in LINK_TARGET.findall(text) if re.search(r"\s", t)]


def unresolved_targets(language: str, relative: Path, text: str) -> list[str]:
    """Relative targets that do not resolve to a file or an index directory."""
    root = ROOT / language
    problems = []
    for raw in targets(text):
        if not raw or raw.startswith(("#", "http://", "https://", "mailto:")):
            continue
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", raw):
            continue  # any other scheme
        if raw.startswith("/"):
            continue  # site-absolute, validated by the strict build
        path = unquote(raw.split("#", 1)[0])
        if not path:
            continue
        parts: list[str] = []
        escaped = False
        for segment in (relative.parent / path).parts:
            if segment == "..":
                if parts:
                    parts.pop()
                else:
                    escaped = True
                    break
            elif segment != ".":
                parts.append(segment)
        if escaped:
            problems.append(f"link escapes docs/{language}: {raw}")
            continue
        candidate = root.joinpath(*parts)
        if candidate.is_file():
            continue
        if candidate.is_dir() and (candidate / "index.md").is_file():
            continue
        problems.append(f"link target not found: {raw}")
    return problems


def unprotected_problems(language: str, relative: Path, text: str) -> list[str]:
    """The protected sections must match the Chinese source verbatim."""
    if relative.parts[:1] != ("作品",) or relative.name == "index.md":
        return []
    source_text = (ROOT / SOURCE / relative).read_text(encoding="utf-8")
    problems = []
    for label, pattern in PROTECTED_SECTIONS.items():
        source_body = section_body(source_text, pattern)
        if source_body is None:
            continue
        body = section_body(text, pattern)
        if body is None:
            problems.append(f"missing protected section ({label})")
        elif body != source_body:
            problems.append(f"protected section drifted ({label})")
    return problems


def segment_index_problems(language: str) -> list[str]:
    """Every `.md` in `{row}/{col}/` must be listed by that segment's index."""
    problems = []
    base = ROOT / language
    for directory in sorted(path for path in base.glob("*/*") if path.is_dir()):
        index = directory / "index.md"
        relative = directory.relative_to(base)
        if not index.is_file():
            problems.append(f"docs/{language}/{relative}: missing index.md")
            continue
        linked = {
            unquote(entry)
            for entry in SEGMENT_INDEX_ENTRY.findall(index.read_text(encoding="utf-8"))
        }
        for page in sorted(directory.glob("*.md")):
            if page.name != "index.md" and page.name not in linked:
                problems.append(
                    f"docs/{language}/{relative}/index.md: {page.name} not listed"
                )
    return problems


def yaml_problems() -> list[str]:
    """YAML parses, list files agree on size, rankings mirror the source."""
    if yaml is None:
        return [
            "PyYAML is missing; run `uvx --with pyyaml python3 scripts/check_i18n.py`"
        ]
    problems: list[str] = []
    item_counts: dict[str, int] = {}

    for language in LANGUAGES:
        for path in sorted((ROOT / language).rglob("*.yaml")):
            relative = path.relative_to(ROOT / language)
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001 - report any parse failure
                problems.append(f"docs/{language}/{relative}: invalid YAML ({exc})")
                continue
            if relative.name != "list.yaml":
                continue
            if not isinstance(data, dict) or not isinstance(data.get("items"), list):
                problems.append(f"docs/{language}/{relative}: missing `items` list")
                continue
            if not isinstance(data.get("title"), str) or not data["title"].strip():
                problems.append(f"docs/{language}/{relative}: missing `title`")
            items = data["items"]
            names: list[str] = []
            for number, item in enumerate(items, start=1):
                if not isinstance(item, dict) or not isinstance(item.get("name"), str):
                    problems.append(
                        f"docs/{language}/{relative}: item #{number} has no `name`"
                    )
                    continue
                missing = {"row", "col", "completeness"} - set(item)
                if missing:
                    problems.append(
                        f"docs/{language}/{relative}: `{item['name']}` missing "
                        f"{', '.join(sorted(missing))}"
                    )
                names.append(item["name"])
            duplicates = sorted({n for n in names if names.count(n) > 1})
            if duplicates:
                problems.append(
                    f"docs/{language}/{relative}: duplicate names "
                    f"{', '.join(duplicates)}"
                )
            item_counts[language] = len(items)

    if len(set(item_counts.values())) > 1:
        problems.append(
            "_meta/list.yaml item counts differ: "
            + ", ".join(f"{lang}={item_counts.get(lang, '?')}" for lang in LANGUAGES)
        )

    ranking = "排名"
    for source in sorted((ROOT / SOURCE / ranking).glob("*.yaml")):
        for language in TARGETS:
            mirror = ROOT / language / ranking / source.name
            label = f"docs/{language}/{ranking}/{source.name}"
            if not mirror.is_file():
                problems.append(f"{label}: missing (copy of docs/{SOURCE}/)")
            elif mirror.read_bytes() != source.read_bytes():
                problems.append(f"{label}: differs from docs/{SOURCE}/{ranking}/")
    return problems


def main() -> int:
    trees = {
        language: {
            path.relative_to(ROOT / language)
            for path in (ROOT / language).rglob("*")
            if path.is_file()
        }
        for language in LANGUAGES
    }

    errors: list[str] = []
    for language in LANGUAGES:
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
            source_text = source_path.read_text(encoding="utf-8")
            translated_text = translated_path.read_text(encoding="utf-8")
            problems = compare(source_text, translated_text)
            problems += unprotected_problems(language, relative, translated_text)
            if problems:
                errors.append(f"docs/{language}/{relative}: {', '.join(problems)}")

    # Link integrity and index coverage are language-independent data checks.
    for language in LANGUAGES:
        for relative in sorted(trees[language]):
            if relative.suffix != ".md":
                continue
            text = (ROOT / language / relative).read_text(encoding="utf-8")
            problems = [f"bare-space target {t!r}" for t in bare_space_targets(text)]
            problems += unresolved_targets(language, relative, text)
            if problems:
                errors.append(f"docs/{language}/{relative}: {', '.join(problems)}")
        errors += segment_index_problems(language)

    errors += yaml_problems()

    if errors:
        print("i18n check failed:", file=sys.stderr)
        print(*(f"  {error}" for error in errors), sep="\n", file=sys.stderr)
        return 1

    count = len(trees[SOURCE])
    print(
        f"i18n trees match ({count} files per language, {checked} pages "
        "structurally checked)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
