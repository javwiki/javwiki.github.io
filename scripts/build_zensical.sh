#!/usr/bin/env bash

set -euo pipefail

summary_file="src/SUMMARY.md"
summary_backup=""

restore_summary() {
  if [[ -n "$summary_backup" && -e "$summary_backup" ]]; then
    mv "$summary_backup" "$summary_file"
  fi
}

trap restore_summary EXIT

# SUMMARY.md is generated for mdBook and would otherwise be rendered as a page
# by Zensical. Keep it available for the existing mdBook workflow afterwards.
if [[ -e "$summary_file" ]]; then
  summary_backup="$(mktemp)"
  mv "$summary_file" "$summary_backup"
fi

uvx --from zensical==0.0.62 zensical build --clean "$@"
