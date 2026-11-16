#!/usr/bin/env python3
"""Stop hook: a deterministic gate. Claude may not finish while the test suite is red.

- Runs only if Python files changed since the last commit. A plain question shouldn't pay for a test run.
- Respects `stop_hook_active`: if Claude is already continuing because of this hook and the tests are still red,
  let it stop instead of looping forever. Claude Code also caps consecutive continuations.
"""

import json
import os
import subprocess
import sys


def python_files_changed() -> bool:
    out = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
    return any(line.rstrip().endswith(".py") for line in out.splitlines())


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    if event.get("stop_hook_active"):
        return 0
    os.chdir(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
    if not python_files_changed():
        return 0
    proc = subprocess.run([sys.executable, "-m", "unittest", "-q"], capture_output=True, text=True, timeout=300)
    if proc.returncode == 0:
        return 0
    tail = "\n".join((proc.stdout + proc.stderr).strip().splitlines()[-15:])
    print(json.dumps({
        "decision": "block",
        "reason": "The test suite is failing, so you are not done. Fix the code (don't edit existing tests), then "
                  "finish. Last lines of `python3 -m unittest`:\n" + tail,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
