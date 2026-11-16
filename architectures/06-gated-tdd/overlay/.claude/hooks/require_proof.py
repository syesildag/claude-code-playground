#!/usr/bin/env python3
"""Stop hook: while a TDD run is active (work/.tdd-active exists), refuse to end until work/proof.html is newer
than the run's start marker.

The Markdown workflow is followed by a model and can skip steps (the course demo forgot the proof page after
context rot). This hook turns the one step that must never be skipped into a deterministic requirement.
"""

import json
import os
import sys
from pathlib import Path


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if event.get("stop_hook_active"):
        return 0
    work = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".") / "work"
    marker, proof = work / ".tdd-active", work / "proof.html"
    if not marker.exists():
        return 0
    if proof.exists() and proof.stat().st_mtime >= marker.stat().st_mtime:
        return 0
    print(json.dumps({
        "decision": "block",
        "reason": "The TDD run is not finished: work/proof.html is missing or older than this run. Complete the "
                  "remaining gates, run `python3 scripts/proof_page.py <ticket>`, add lessons to docs/lessons.md, "
                  "then `rm work/.tdd-active`. If you are blocked, explain why and remove the marker.",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
