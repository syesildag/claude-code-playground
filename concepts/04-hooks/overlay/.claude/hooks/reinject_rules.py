#!/usr/bin/env python3
"""SessionStart(compact) hook: after the conversation is compacted, re-inject the rules that must survive.

The course's middle level of control: an instruction in CLAUDE.md can get diluted, so a hook re-injects it at the
right moment. Stronger, but still probabilistic. Only a gate (exit 2) guarantees anything.
"""

import json
import os
import sys
from pathlib import Path


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        event = {}
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
    rules = project / ".claude" / "critical-rules.md"
    if rules.exists():
        text = "Re-injected after compaction. These rules still apply:\n" + rules.read_text(encoding="utf-8")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
