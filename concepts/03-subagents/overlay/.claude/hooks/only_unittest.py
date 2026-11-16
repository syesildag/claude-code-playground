#!/usr/bin/env python3
"""PreToolUse hook scoped to the test-runner agent (declared in its frontmatter).

It only runs while test-runner is active, and it lets test-runner run the test suite and nothing else.
"""

import json
import re
import sys

ALLOWED = re.compile(r"^(cd\s+\S+\s*&&\s*)?python3? -m unittest(\s|$)")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (event.get("tool_input") or {}).get("command", "").strip()
    if ALLOWED.match(command):
        return 0
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"test-runner may only run `python3 -m unittest ...`, not: {command[:80]}",
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
