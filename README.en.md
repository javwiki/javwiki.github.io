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

The local maintenance environment uses Python 3.12.14 and uv 0.12.5. On first use, install dependencies from the lockfile:

```bash
uv sync --locked --no-dev
uv run --locked --no-dev zensical build --config-file zensical.ja.toml --clean
uv run --locked --no-dev zensical build --config-file zensical.toml --clean
uv run --locked --no-dev zensical build --config-file zensical.en.toml --clean
```

The build output is in `site/`. Start a local preview:

```bash
uv run --locked --no-dev zensical serve --config-file zensical.ja.toml
```

Use `zensical.toml` or `zensical.en.toml` to preview Chinese or English, respectively. Japanese is published at `/` (the default language), Chinese at `/zh/`, and English at `/en/`. The language selector in the header switches between editions. All three configurations enable `navigation.prune` to avoid embedding the full site navigation in every page; `overrides/` generates links to each page's language counterparts.

Chinese (`docs/zh/`) is the source content; the Japanese and English directories contain its translations. Relative paths and filenames are identical across all three languages.

Translation methods, structural requirements, quality limitations, and ongoing maintenance conventions are documented in the [translation and maintenance guide](maintenance/TRANSLATION.md).

## Automatic publishing

CI follows the [official Zensical GitHub Pages workflow](https://zensical.org/docs/publish-your-site/), defined in [.github/workflows/zensical.yml](.github/workflows/zensical.yml): configure Pages, check out the repository, install Python and dependencies, build the three editions sequentially, upload the entire `site/` directory, and deploy. Publishing runs on pushes to `master` or `main`. Set the repository’s Pages publishing source to **GitHub Actions**.

Build Japanese into `site/` first, then Chinese into `site/zh/` and English into `site/en/`. CI does not invoke maintenance scripts or run index checks, cross-language validation, HTML link checks, pytest, Ruff, or dependency audits. It also omits `--strict` and build caching. Maintainers run these checks manually. CI uses `ubuntu-latest`, Python `3.x`, and Actions major-version tags, and runs `pip install zensical` directly. It does not use `uv.lock`, exact version pins, manual triggers, or additional branch guards. The only adaptation of the official example is expanding its single build into three language builds.

## Manual validation and tests

`./scripts/build_site.sh` is the manual full-validation entry point: check that indexes and navigation are up to date, validate the three content trees, build all editions in strict mode, then check generated links, anchors, language switching, and size budgets. It does not deploy and is not called by CI.

```bash
./scripts/build_site.sh
```

Checks, tests, formatting checks, and dependency audits can also be run individually. Build all three editions before running `check_site.py`:

```bash
uv run --locked --no-dev python scripts/content/generate_indexes.py --check
uv run --locked --no-dev python scripts/checks/check_i18n.py
uv run --locked --no-dev python scripts/checks/check_site.py
uv run --locked --group dev --group scraper pytest
uv run --locked --group dev ruff format --check scripts/checks scripts/content scrapers/fanza/spider.py tests
uv run --locked --group dev ruff check scripts/checks scripts/content scrapers/fanza/spider.py tests
uv run --locked --group dev --group scraper pip-audit
```

`check_i18n.py` verifies that files correspond across the three language directories, and compares Japanese and English pages against their Chinese sources for front matter, heading hierarchy, link targets, table shape, and code blocks. It also checks relative links, complete syllabary index coverage, mappings between performer lists and actual pages, ranking schemas and their copies in all three languages, and exact matches for protected sections of work pages. `./scripts/build_site.sh` runs this check first, then uses `check_site.py` to validate internal links and anchors after building all three editions. Both checks are run manually.

`check_i18n.py` checks structure, not meaning. Cross-language content review—aligning body text, comparing numbers and dates, checking proper names, and finding untranslated text—is currently manual. The method and results of the translation review are recorded in the cross-language proofreading section (「跨语言校对」) of the [translation and maintenance guide](maintenance/TRANSLATION.md). `python3 scripts/i18n/en_fix_name_openings.py` aligns display names in English body text and is idempotent; add `--check` to report changes without applying them.

Local maintenance dependencies for Python, Zensical, validation tools, and scrapers are declared in `pyproject.toml`, with exact versions pinned in `uv.lock`. Automatic publishing uses the official pip installation method and does not read this lockfile.
