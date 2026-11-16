#!/usr/bin/env python3
"""PreToolUse(Edit|Write|MultiEdit) hook: allow writes only under the directory prefixes given as arguments.

Used in agent frontmatter to enforce separation of powers, e.g. the planner may only write in work/:
    command: python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/scoped_writes.py" work/
"""

import json
import os
import sys
from pathlib import Path


def main() -> int:
    allowed = [a.rstrip("/") + "/" for a in sys.argv[1:]]
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    raw = (event.get("tool_input") or {}).get("file_path", "")
    if not raw or not allowed:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".").resolve()
    path = Path(raw) if Path(raw).is_absolute() else project / raw
    try:
        rel = path.resolve().relative_to(project).as_posix()
    except ValueError:
        rel = str(path)
    if any(rel.startswith(prefix) for prefix in allowed):
        return 0
    who = event.get("agent_type") or "this agent"
    print(f"scoped_writes.py: {who} may only write under {', '.join(allowed)}, not {rel}.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
