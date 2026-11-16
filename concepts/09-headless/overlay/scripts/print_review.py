#!/usr/bin/env python3
"""Pretty-print a headless review result and exit 1 on request_changes (a CI gate)."""

import json
import sys
from pathlib import Path


def structured(result: dict) -> dict:
    """With --json-schema the validated object is in `structured_output`. Fall back to parsing `result`."""
    if isinstance(result.get("structured_output"), dict):
        return result["structured_output"]
    try:
        return json.loads(result.get("result") or "{}")
    except json.JSONDecodeError:
        return {}


def main() -> int:
    text = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
    result = json.loads(text.splitlines()[-1]) if text else {}
    review = structured(result)
    if not review:
        print("No structured review found. Raw result:\n" + str(result.get("result"))[:1000])
        return 2
    icons = {"blocking": "✘", "minor": "⚠", "note": "·"}
    for f in review.get("findings", []):
        print(f"{icons.get(f.get('severity'), '?')} [{f.get('severity')}] {f.get('location')}: {f.get('issue')}")
        if f.get("fix"):
            print(f"    fix: {f['fix']}")
    cost = result.get("total_cost_usd")
    print(f"\nverdict: {review.get('verdict')} · turns {result.get('num_turns')} · "
          f"cost ${cost:.4f}" if isinstance(cost, (int, float)) else f"\nverdict: {review.get('verdict')}")
    return 1 if review.get("verdict") == "request_changes" else 0


if __name__ == "__main__":
    sys.exit(main())
