#!/usr/bin/env python3
"""UserPromptSubmit hook: runs on every prompt before Claude sees it.

- Blocks prompts that contain something that looks like a secret, so it never reaches the model.
- When the prompt mentions a ticket id (T01, T02, ...), attaches the ticket's path and a reminder as context.
"""

import json
import os
import re
import sys
from pathlib import Path

SECRET = re.compile(r"\b(AKIA[0-9A-Z]{16}|sk-ant-[A-Za-z0-9_\-]{20,}|gh[pousr]_[A-Za-z0-9]{36,})")
TICKET = re.compile(r"\bT(\d{2})\b", re.I)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    prompt = event.get("prompt", "")
    if SECRET.search(prompt):
        print(json.dumps({
            "decision": "block",
            "reason": "prompt_guard.py: your prompt seems to contain a secret (API key or token). It was NOT sent "
                      "to the model. Remove it and use an environment variable instead.",
        }))
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
    tickets = []
    for number in sorted(set(TICKET.findall(prompt))):
        tickets += [str(p.relative_to(project)) for p in (project / "tickets").glob(f"T{number}-*.md")]
    if tickets:
        context = (f"The user referred to {', '.join(tickets)}. Read it first. Its acceptance criteria are the "
                   "definition of done, and its out-of-scope list is binding.")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
