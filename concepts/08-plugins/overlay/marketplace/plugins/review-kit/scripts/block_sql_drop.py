#!/usr/bin/env python3
"""review-kit policy hook: block destructive SQL in shell commands (exit 2 + stderr reason).

Shipped inside the plugin, the policy travels with every install. It's deterministic and costs zero tokens.
"""

import json
import re
import sys

DESTRUCTIVE = re.compile(r"(?i)\b(drop\s+(table|database|schema)|truncate\s+table)\b")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (event.get("tool_input") or {}).get("command", "")
    match = DESTRUCTIVE.search(command)
    if match:
        print(f"review-kit policy: '{match.group(0)}' is never run by an agent. Ask a human DBA.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
