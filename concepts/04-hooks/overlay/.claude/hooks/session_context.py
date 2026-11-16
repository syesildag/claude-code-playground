#!/usr/bin/env python3
"""SessionStart hook: hand Claude live facts at launch (branch, dirty files, test status) as additionalContext.

Cheaper than Claude discovering them with three tool calls, and always fresh, unlike text in CLAUDE.md.
"""

import json
import os
import subprocess
import sys


def run(*cmd: str) -> str:
    return subprocess.run(list(cmd), capture_output=True, text=True, timeout=120).stdout.strip()


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        event = {}
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
    branch = run("git", "branch", "--show-current") or "(no branch)"
    dirty = [line for line in run("git", "status", "--porcelain").splitlines() if line.strip()]
    proc = subprocess.run([sys.executable, "-m", "unittest", "-q"], capture_output=True, text=True, timeout=300)
    lines = [line for line in (proc.stdout + proc.stderr).splitlines() if line.strip()]
    tests = lines[-1] if lines else "unknown"
    context = (
        f"Session facts (from the SessionStart hook): branch `{branch}`; {len(dirty)} uncommitted file(s); "
        f"test suite: {tests}. Tickets live in tickets/."
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
