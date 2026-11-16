#!/usr/bin/env bash
# Run the single-agent review and the fan-out review headlessly on the same code, then score both.
#   bash scripts/compare-reviews.sh            MODEL=sonnet BUDGET=3 bash scripts/compare-reviews.sh
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
mkdir -p work .claude/logs
settings='{"permissions":{"allow":["Write(./work/**)","Edit(./work/**)"]}}'

run() {  # $1 = skill name
  local start end
  start=$(date +%s)
  claude -p "/$1 taskboard/" --setting-sources project,local --settings "$settings" \
    --model "${MODEL:-sonnet}" --permission-mode acceptEdits --permission-prompts none \
    --max-budget-usd "${BUDGET:-2}" --output-format json < /dev/null > ".claude/logs/$1.json"
  end=$(date +%s)
  mv work/review.md "work/review-$1.md" 2>/dev/null || echo "(no work/review.md produced by /$1)"
  python3 - "$1" "$((end - start))" <<'EOF'
import json, sys
name, seconds = sys.argv[1], sys.argv[2]
d = json.loads(open(f".claude/logs/{name}.json").read().strip().splitlines()[-1])
per_model = ", ".join(f"{m}: ${u.get('costUSD', 0):.3f}" for m, u in (d.get("modelUsage") or {}).items())
print(f"\n== /{name}: {seconds}s · turns {d.get('num_turns')} · ${d.get('total_cost_usd', 0):.3f} ({per_model})")
EOF
  [ -f "work/review-$1.md" ] && python3 scripts/score_review.py "work/review-$1.md"
}

run single-review
run multi-review
