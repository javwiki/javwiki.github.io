#!/usr/bin/env python3
"""Guard the trilingual content trees against drift.

Chinese (`docs/zh/`) is the source of the truth. The Japanese and English
editions are translations of it and must stay structurally identical to it:
same file set, same front matter, same heading hierarchy, same link targets,
same table shape, same code fences. Only prose is translated.

On top of the structural comparison it enforces data integrity that the
structural pass alone cannot see:

* link targets keep document order, are complete (no bare-space truncation),
  and resolve to a file
* code-fence languages stay aligned with the Chinese source
* every `.md` in a segment directory is listed in that segment's `index.md`
* `_meta/list.yaml`, `_meta/list.md`, and the real actress pages agree
* `排名/*.yaml` pass their schema and stay byte-identical to the Chinese source
* protected official-source sections stay byte-identical to the Chinese source
* active HTML (scripts, frames, forms, event handlers) is rejected outside code fences

Run directly (`uv run --locked --no-dev python scripts/check_i18n.py`) or via
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
UNSAFE_HTML = re.compile(
    r"<\s*(?:script|iframe|object|embed|form)\b|\bon[a-z]+\s*=|javascript\s*:",
    re.I,
)

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

# Work pages are protected by category; JAE is the one event page that keeps
# the same official-source/Chinese-translation pair outside that category.
PROTECTED_PAGES = frozenset({Path("活动/JAE.md")})

LIST_ITEM_FIELDS = ("name", "row", "col", "completeness")
RANKING_FIELDS = (
    "source",
    "type",
    "url",
    "fetched_at",
    "count",
    "rankings",
)
RANKING_ITEM_FIELDS = (
    "rank",
    "actress_id",
    "name",
    "image",
    "contents_count",
    "latest_content_id",
    "latest_title",
)


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
    matches = [
        (match.start(), pattern_index, match.group(1))
        for pattern_index, pattern in enumerate((LINK, AUTOLINK, IMG_SRC))
        for match in pattern.finditer(text)
    ]
    return [target for _, _, target in sorted(matches)]


def fence_languages(text: str) -> list[str]:
    """Language/info token of each opening code fence, in document order."""
    languages = []
    opening: tuple[str, int] | None = None

    for line in text.splitlines():
        match = FENCE.match(line)
        if not match:
            continue
        marker = match.group(0)
        fence_type = marker[0]
        if opening is None:
            opening = (fence_type, len(marker))
            info = line[len(marker) :].strip()
            languages.append(info.split(maxsplit=1)[0] if info else "")
        elif fence_type == opening[0] and len(marker) >= opening[1]:
            opening = None

    return languages


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
    if fence_languages(source) != fence_languages(translated):
        problems.append("code fence languages")
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
    rest = text[newline + 1 :] if newline >= 0 else ""
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
    is_work = relative.parts[:1] == ("作品",) and relative.name != "index.md"
    if not is_work and relative not in PROTECTED_PAGES:
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


def markdown_list_names(text: str) -> list[str]:
    """Top-level plain bullet names in `_meta/list.md`, excluding code fences."""
    names = []
    opening: tuple[str, int] | None = None
    for line in text.splitlines():
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(0)
            if opening is None:
                opening = (marker[0], len(marker))
            elif marker[0] == opening[0] and len(marker) >= opening[1]:
                opening = None
            continue
        if opening is not None:
            continue
        item = re.match(r"^- ([^\n]+?)\s*$", line)
        if item:
            names.append(item.group(1).strip())
    return names


def list_schema_problems(data: object) -> list[str]:
    """Validate the actress-list title and item fields."""
    if not isinstance(data, dict):
        return ["root must be a mapping"]
    if not isinstance(data.get("title"), str) or not data["title"].strip():
        return ["missing non-empty `title`"]

    items = data.get("items")
    if not isinstance(items, list):
        return ["missing `items` list"]

    problems = []
    names = []
    for number, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            problems.append(f"item #{number} must be a mapping")
            continue
        for field in LIST_ITEM_FIELDS:
            value = item.get(field)
            if field not in item:
                problems.append(f"item #{number} missing `{field}`")
            elif not isinstance(value, str) or not value.strip():
                problems.append(f"item #{number} has invalid `{field}`")
        name = item.get("name")
        if isinstance(name, str) and name.strip():
            names.append(name)

    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        problems.append("duplicate names " + ", ".join(duplicates))
    return problems


def list_mapping_problems(
    language: str,
    items: list[dict],
    list_text: str,
    source_items: list[dict],
    root: Path,
) -> list[str]:
    """Validate list.md, the canonical page paths, and shared item metadata."""
    problems = []
    yaml_names = [item["name"] for item in items]
    markdown_names = markdown_list_names(list_text)
    if yaml_names != markdown_names:
        first = next(
            (
                number
                for number, pair in enumerate(
                    zip(yaml_names, markdown_names, strict=False), 1
                )
                if pair[0] != pair[1]
            ),
            min(len(yaml_names), len(markdown_names)) + 1,
        )
        problems.append(f"_meta/list.md differs from list.yaml at item #{first}")

    expected = {
        Path(item["row"], item["col"], f"{item['name']}.md") for item in source_items
    }
    base = root / language
    actual = {
        path.relative_to(base)
        for path in base.glob("*/*/*.md")
        if path.name != "index.md"
    }
    for path in sorted(expected - actual):
        problems.append(f"list.yaml page not found: {path}")
    for path in sorted(actual - expected):
        problems.append(f"unlisted actress page: {path}")

    if len(source_items) == len(items):
        for number, (source, target) in enumerate(
            zip(source_items, items, strict=True), start=1
        ):
            for field in ("row", "col", "completeness"):
                if source[field] != target[field]:
                    problems.append(
                        f"item #{number} `{field}` differs from "
                        f"docs/{SOURCE}/_meta/list.yaml"
                    )
    return problems


def ranking_problems(data: object) -> list[str]:
    """Validate a FANZA ranking document and the identity/order of its rows."""
    if not isinstance(data, dict):
        return ["root must be a mapping"]

    problems = [f"missing `{field}`" for field in RANKING_FIELDS if field not in data]
    for field in ("source", "type", "url", "fetched_at"):
        value = data.get(field)
        if field in data and (not isinstance(value, str) or not value.strip()):
            problems.append(f"invalid `{field}`")

    count = data.get("count")
    if "count" in data and (type(count) is not int or count < 0):
        problems.append("invalid `count`")

    rankings = data.get("rankings")
    if "rankings" in data and not isinstance(rankings, list):
        problems.append("`rankings` must be a list")
        return problems
    if not isinstance(rankings, list):
        return problems
    if not rankings:
        problems.append("`rankings` must not be empty")

    ranks = []
    actress_ids = []
    for number, item in enumerate(rankings, start=1):
        if not isinstance(item, dict):
            problems.append(f"ranking item #{number} must be a mapping")
            continue
        missing = [field for field in RANKING_ITEM_FIELDS if field not in item]
        if missing:
            problems.append(f"ranking item #{number} missing {', '.join(missing)}")
        for field in ("rank", "contents_count"):
            value = item.get(field)
            if field in item and (type(value) is not int or value < 0):
                problems.append(f"ranking item #{number} has invalid `{field}`")
        for field in (
            "actress_id",
            "name",
            "image",
            "latest_content_id",
            "latest_title",
        ):
            value = item.get(field)
            if field in item and (not isinstance(value, str) or not value.strip()):
                problems.append(f"ranking item #{number} has invalid `{field}`")
        if type(item.get("rank")) is int:
            ranks.append(item["rank"])
        if isinstance(item.get("actress_id"), str) and item["actress_id"].strip():
            actress_ids.append(item["actress_id"])

    expected_ranks = list(range(1, len(rankings) + 1))
    if ranks != expected_ranks:
        problems.append("ranking rows must contain ordered ranks 1..count")
    duplicates = sorted(
        actress_id
        for actress_id in set(actress_ids)
        if actress_ids.count(actress_id) > 1
    )
    if duplicates:
        problems.append("duplicate actress_id " + ", ".join(duplicates))
    if type(count) is int and count != len(rankings):
        problems.append("`count` does not match the number of ranking rows")
    return problems


def unsafe_html_problems(relative: Path, text: str) -> list[str]:
    """Reject active HTML in Markdown source; prose and code fences are allowed."""
    problems = []
    opening: tuple[str, int] | None = None
    for number, line in enumerate(text.splitlines(), start=1):
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(0)
            if opening is None:
                opening = (marker[0], len(marker))
            elif marker[0] == opening[0] and len(marker) >= opening[1]:
                opening = None
            continue
        if opening is not None:
            continue
        match = UNSAFE_HTML.search(line)
        if match:
            problems.append(
                f"docs/{relative}:{number}: unsafe HTML ({match.group(0)!r})"
            )
    return problems


def yaml_problems(root: Path | None = None) -> list[str]:
    """Validate list/ranking schemas and ensure translated data mirrors zh."""
    if yaml is None:
        return [
            "PyYAML is missing; run "
            "`uv run --locked --no-dev python scripts/check_i18n.py`"
        ]
    root = ROOT if root is None else root
    problems: list[str] = []
    item_counts: dict[str, int] = {}
    lists: dict[str, list[dict]] = {}

    for language in LANGUAGES:
        base = root / language
        for path in sorted(base.rglob("*.yaml")):
            relative = path.relative_to(base)
            label = f"docs/{language}/{relative}"
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                problems.append(f"{label}: invalid YAML ({exc})")
                continue

            if relative == Path("_meta/list.yaml"):
                schema_problems = list_schema_problems(data)
                problems.extend(f"{label}: {problem}" for problem in schema_problems)
                if not schema_problems:
                    items = data["items"]
                    lists[language] = items
                    item_counts[language] = len(items)
            elif language == SOURCE and relative.parts[0] == "排名":
                problems.extend(
                    f"{label}: {problem}" for problem in ranking_problems(data)
                )

    if len(set(item_counts.values())) > 1:
        problems.append(
            "_meta/list.yaml item counts differ: "
            + ", ".join(f"{lang}={item_counts.get(lang, '?')}" for lang in LANGUAGES)
        )

    source_items = lists.get(SOURCE)
    if source_items is not None:
        for language in LANGUAGES:
            items = lists.get(language)
            if items is None:
                continue
            list_path = root / language / "_meta/list.md"
            if not list_path.is_file():
                problems.append(f"docs/{language}/_meta/list.md: missing")
                continue
            list_text = list_path.read_text(encoding="utf-8")
            problems.extend(
                f"docs/{language}/_meta/list.yaml: {problem}"
                for problem in list_mapping_problems(
                    language, items, list_text, source_items, root
                )
            )

    ranking = "排名"
    for source in sorted((root / SOURCE / ranking).glob("*.yaml")):
        for language in TARGETS:
            mirror = root / language / ranking / source.name
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
            problems += unsafe_html_problems(relative, text)
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
