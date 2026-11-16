#!/usr/bin/env python3
"""PreToolUse(Edit|Write|MultiEdit|NotebookEdit): protect files the agent must never touch.

Style shown here: exit code 2 blocks the call, and stderr becomes the reason Claude sees.

Rules:
- `.env*` files (secrets) are never edited.
- Existing tests are never modified: the classic "make the test pass by editing the test" shortcut.
  *New* test files may be created, because adding tests is good.
- Create `.claude/allow-test-edits` to lift the test rule temporarily: a hook reading state from a file.
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
    tool_input = event.get("tool_input") or {}
    raw = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not raw:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".").resolve()
    path = Path(raw) if Path(raw).is_absolute() else project / raw
    try:
        rel = path.resolve().relative_to(project)
    except ValueError:
        return 0  # outside the project: not this hook's business

    if rel.name.startswith(".env"):
        print(f"protect_files.py: {rel} holds secrets and must not be edited by the agent.", file=sys.stderr)
        return 2

    is_existing_test = rel.parts[:1] == ("tests",) and path.exists()
    if is_existing_test and not (project / ".claude" / "allow-test-edits").exists():
        print(
            f"protect_files.py: {rel} is an existing test. Fix the code instead of the test. If the test itself is "
            "wrong, explain why and ask the user (they can create .claude/allow-test-edits). "
            "Adding NEW test files is allowed.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
