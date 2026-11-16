#!/usr/bin/env bash
# Headless, read-only, budget-capped review that returns JSON matching schemas/review.schema.json.
# Exit code 1 when the verdict is request_changes, so CI can use it as a gate.
#
#   bash scripts/headless-review.sh [file]          MODEL=sonnet BUDGET=0.50 bash scripts/headless-review.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
target="${1:-taskboard/report.py}"
mkdir -p .claude/logs
prompt="$(sed "s|{{TARGET}}|${target}|g" prompts/review.md)"

# --tools limits which built-in tools exist at all (stronger than allow rules): this run cannot edit or run shell.
claude -p "$prompt" \
  --setting-sources project,local \
  --model "${MODEL:-haiku}" \
  --tools "Read,Grep,Glob" \
  --permission-prompts none \
  --max-budget-usd "${BUDGET:-0.25}" \
  --output-format json \
  --json-schema "$(cat schemas/review.schema.json)" \
  < /dev/null > .claude/logs/last-review.json

python3 scripts/print_review.py .claude/logs/last-review.json
