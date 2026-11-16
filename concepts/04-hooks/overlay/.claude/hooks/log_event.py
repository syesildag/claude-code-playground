#!/usr/bin/env python3
"""Observer hook: registered on every lifecycle event, it logs one line per event. It never changes anything.

Watch the agent loop live from a second terminal:   tail -f .claude/logs/events.log
Raw events (to learn each event's JSON schema):     .claude/logs/events.jsonl
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def short(text: object, limit: int = 70) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def summarize(event: dict) -> str:
    name = event.get("hook_event_name", "?")
    tool_input = event.get("tool_input") or {}
    if name in ("PreToolUse", "PostToolUse", "PostToolUseFailure", "PermissionRequest", "PermissionDenied"):
        detail = tool_input.get("command") or tool_input.get("file_path") or tool_input.get("pattern") \
            or tool_input.get("description") or ""
        return f"{event.get('tool_name', '?'):<10} {short(detail)}"
    if name == "UserPromptSubmit":
        return short(event.get("prompt", ""))
    if name in ("SessionStart", "SessionEnd"):
        return str(event.get("source") or event.get("reason") or "")
    if name in ("SubagentStart", "SubagentStop"):
        return f"{event.get('agent_type', '?')} ({str(event.get('agent_id', ''))[:8]})"
    if name in ("PreCompact", "PostCompact"):
        return str(event.get("trigger", ""))
    if name == "Notification":
        return short(event.get("message", ""))
    if name == "Stop":
        return f"stop_hook_active={event.get('stop_hook_active')}"
    return ""


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    project = Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or ".")
    logs = project / ".claude" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    who = f"[{event['agent_type']}] " if event.get("agent_type") else ""
    line = f"{datetime.now():%H:%M:%S}  {event.get('hook_event_name', '?'):<17} {who}{summarize(event)}"
    with (logs / "events.log").open("a", encoding="utf-8") as fh:
        fh.write(line.rstrip() + "\n")
    with (logs / "events.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
    return 0  # silent: on SessionStart/UserPromptSubmit, anything printed would be added to Claude's context


if __name__ == "__main__":
    sys.exit(main())
