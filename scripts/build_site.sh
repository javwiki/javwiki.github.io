#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(dirname "$SCRIPT_DIR")
cd "$ROOT_DIR"

uv run --locked --no-dev python scripts/content/generate_indexes.py --check
uv run --locked --no-dev python scripts/checks/check_i18n.py
uv run --locked --no-dev zensical build --config-file zensical.ja.toml --clean --strict
uv run --locked --no-dev zensical build --config-file zensical.toml --clean --strict
uv run --locked --no-dev zensical build --config-file zensical.en.toml --clean --strict
uv run --locked --no-dev python scripts/checks/check_site.py
