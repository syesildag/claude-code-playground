#!/usr/bin/env python3
"""PreToolUse(Bash): deny destructive or gate-bypassing shell commands.

Style shown here: exit 0 + a JSON `permissionDecision: "deny"`. The reason goes back to Claude, which adapts.
(Compare protect_files.py, which uses the other style: exit code 2 + stderr.)
"""

import json
import re
import sys

RULES = [
    (r"\brm\s+(-\w*r\w*f|-\w*f\w*r)\b", "recursive force delete. Remove specific files instead"),
    (r"\bgit\s+push\b.*(--force\b|\s-f\b|--force-with-lease)", "force push rewrites shared history"),
    (r"--no-verify\b", "--no-verify skips the git hooks that guard this repo"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard throws away uncommitted work"),
    (r"(?i)\bdrop\s+(table|database)\b", "dropping tables/databases is never done by the agent"),
    (r"\b(curl|wget)\b[^|]*\|\s*(ba|z)?sh\b", "piping a download into a shell runs unreviewed code"),
    (r"\bchmod\s+(-R\s+)?777\b", "world-writable permissions"),
]


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (event.get("tool_input") or {}).get("command", "")
    for pattern, reason in RULES:
        if re.search(pattern, command):
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked by block_dangerous_bash.py: {reason}.",
                }
            }))
            return 0
    return 0  # no output = no opinion; normal permission rules apply


if __name__ == "__main__":
    sys.exit(main())
