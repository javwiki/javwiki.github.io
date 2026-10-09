# JAV Encyclopedia

[中文](README.md) | [日本語](README.ja.md) | [English](README.en.md)

This repository uses Zensical to build Chinese, Japanese, and English editions of the encyclopedia. Content lives in `docs/zh/`, `docs/ja/`, and `docs/en/`, with matching relative paths.

## Directory structure and maintenance

Public content is organized into people, works, industry, reference material, and topics. All three languages share the same paths. Actress entries ordered by Japanese syllabary are located in `docs/{lang}/人物/女优/{行}/{段}/`; production companies and labels are stored separately in `产业/制作公司/` and `产业/厂牌/`.

Maintenance notes, translation conventions, lists, and name mappings are kept in [maintenance/](maintenance/README.md) and are excluded from the published site. Scripts are grouped by purpose into `scripts/checks/`, `scripts/content/`, `scripts/i18n/`, and `scripts/legacy/`; see the [script documentation](scripts/README.md).

After adding or moving pages, or changing classification metadata, regenerate indexes and the full navigation:

```bash
uv run --locked --no-dev python scripts/content/generate_indexes.py
```

## Local preview

Local tools or scraping tasks that need a proxy with a Japanese exit IP can use the [Docker proxy configuration](docker/japan-vpn/README.md). Supply your own subscription for Japanese proxy nodes.

For the proxy-based scraping, validation, and publication of FANZA monthly rankings, including execution records, see the [Japanese proxy scraping guide](scrapers/fanza/JAPAN_PROXY.md).

The project uses Python 3.12.14 and uv 0.12.5. On first use, install dependencies from the lockfile:

```bash
uv sync --locked --no-dev
./scripts/build_site.sh
```

The build output is in `site/`. Start a local preview:

```bash
uv run --locked --no-dev zensical serve --config-file zensical.ja.toml
```

Use `zensical.toml` or `zensical.en.toml` to preview Chinese or English, respectively. Japanese is published at `/` (the default language), Chinese at `/zh/`, and English at `/en/`. The language selector in the header switches between editions. All three configurations enable `navigation.prune` to avoid embedding the full site navigation in every page; `overrides/` generates links to each page's language counterparts.

Chinese (`docs/zh/`) is the source content; the Japanese and English directories contain its translations. Relative paths and filenames are identical across all three languages.

Translation methods, structural requirements, quality limitations, and ongoing maintenance conventions are documented in the [translation and maintenance guide](maintenance/TRANSLATION.md).

## Validation and tests

```bash
uv run --locked --no-dev python scripts/checks/check_i18n.py
uv run --locked --group dev --group scraper pytest
uv run --locked --group dev ruff format --check scripts/checks scripts/content scrapers/fanza/spider.py tests
uv run --locked --group dev ruff check scripts/checks scripts/content scrapers/fanza/spider.py tests
uv run --locked --group dev --group scraper pip-audit
```

`check_i18n.py` verifies that files correspond across the three language directories, and compares Japanese and English pages against their Chinese sources for front matter, heading hierarchy, link targets, table shape, and code blocks. It also checks relative links, complete syllabary index coverage, mappings between performer lists and actual pages, ranking schemas and their copies in all three languages, and exact matches for protected sections of work pages. Both `./scripts/build_site.sh` and CI run this check first. After all three editions are built, `check_site.py` validates internal links and anchors in the generated pages.

`check_i18n.py` checks structure, not meaning. Cross-language content review—aligning body text, comparing numbers and dates, checking proper names, and finding untranslated text—is currently manual. The method and results of the translation review are recorded in the cross-language proofreading section (「跨语言校对」) of the [translation and maintenance guide](maintenance/TRANSLATION.md). `python3 scripts/i18n/en_fix_name_openings.py` aligns display names in English body text and is idempotent; add `--check` to report changes without applying them.

Dependencies for Python, Zensical, validation tools, and scrapers are declared in `pyproject.toml`, with exact versions pinned in `uv.lock`. CI uses `--locked`, so dependencies are not silently updated during builds.
