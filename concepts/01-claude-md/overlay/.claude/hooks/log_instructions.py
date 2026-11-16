#!/usr/bin/env python3
"""InstructionsLoaded hook: log every CLAUDE.md / rules file at the moment it enters Claude's context.

Watch it live from a second terminal:   tail -f .claude/logs/instructions.log
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def pick(event: dict, preferred: str, fragment: str) -> str:
    """Field names can change between versions, so fall back to any key that looks right."""
    if isinstance(event.get(preferred), str):
        return event[preferred]
    for key, value in event.items():
        if fragment in key and key != "transcript_path" and isinstance(value, str):
            return value
    return "?"


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
    logs = project / ".claude" / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    path = pick(event, "file_path", "path")
    reason = pick(event, "load_reason", "reason")
    try:
        path = os.path.relpath(path, project) if path != "?" else path
    except ValueError:
        pass

    with (logs / "instructions.log").open("a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now():%H:%M:%S}  {reason:<18} {path}\n")
    with (logs / "instructions.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
    return 0  # print nothing: this hook only observes


if __name__ == "__main__":
    sys.exit(main())
