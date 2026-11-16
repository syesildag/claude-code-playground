#!/usr/bin/env python3
"""PostToolUse(Edit|Write|MultiEdit): compile every Python file right after Claude edits it.

The edit already happened, so this hook can't block it. `decision: "block"` puts the error next to the tool result,
so Claude fixes it on its next step instead of discovering it three edits later. Projects often run a formatter
or linter (ruff, prettier) here.
"""

import json
import subprocess
import sys


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    path = (event.get("tool_input") or {}).get("file_path", "")
    if not path.endswith(".py"):
        return 0
    proc = subprocess.run([sys.executable, "-m", "py_compile", path], capture_output=True, text=True)
    if proc.returncode != 0:
        print(json.dumps({"decision": "block",
                          "reason": f"check_python.py: {path} no longer compiles:\n{proc.stderr.strip()[-800:]}"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
