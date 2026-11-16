#!/usr/bin/env python3
"""A complete MCP server in plain stdlib Python, no SDK. It shows that MCP is just JSON-RPC 2.0.

Transport: stdio. Claude Code starts this process and exchanges one JSON object per line on stdin/stdout.
Everything the server prints to stdout must be protocol. Logs go to stderr or a file.

Exposes:
  tools    list_tasks, add_task, move_task, board_stats   → appear as mcp__taskboard__<name>
  prompts  standup                                        → appears as the slash command /mcp__taskboard__standup

Every message is logged to .claude/logs/mcp-taskboard.log so you can watch the protocol.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from taskboard import STATUSES, JsonStore, TaskBoard  # noqa: E402

SERVER_INFO = {"name": "taskboard", "version": "1.0.0"}
FALLBACK_PROTOCOL = "2025-06-18"
LOG = ROOT / ".claude" / "logs" / "mcp-taskboard.log"

TOOLS = [
    {
        "name": "list_tasks",
        "description": "List the tasks on the board, optionally only those with a given status.",
        "inputSchema": {"type": "object", "properties": {"status": {"type": "string", "enum": list(STATUSES)}},
                        "additionalProperties": False},
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "add_task",
        "description": "Add a task to the board. Returns the new task's id.",
        "inputSchema": {"type": "object", "properties": {"title": {"type": "string", "minLength": 1}},
                        "required": ["title"], "additionalProperties": False},
    },
    {
        "name": "move_task",
        "description": "Move a task to another status column.",
        "inputSchema": {"type": "object",
                        "properties": {"id": {"type": "integer"}, "status": {"type": "string", "enum": list(STATUSES)}},
                        "required": ["id", "status"], "additionalProperties": False},
    },
    {
        "name": "board_stats",
        "description": "Progress summary: total, done and open task counts.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True},
    },
]

PROMPTS = [{"name": "standup", "description": "Draft today's stand-up update from the board", "arguments": []}]


def log(direction: str, payload: dict) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now():%H:%M:%S} {direction} {json.dumps(payload)[:500]}\n")
    except OSError:
        pass


def board() -> TaskBoard:
    return TaskBoard(JsonStore(os.environ.get("TASKBOARD_DB") or ROOT / "board.json"))


def call_tool(name: str, args: dict) -> tuple[str, bool]:
    """Return (text, is_error). Tool failures are results with isError, not protocol errors."""
    try:
        if name == "list_tasks":
            tasks = board().list(args.get("status"))
            return ("\n".join(f"#{t.id} [{t.status}] {t.title}" for t in tasks) or "The board is empty."), False
        if name == "add_task":
            task = board().add(args["title"])
            return f"Added task #{task.id}: {task.title}", False
        if name == "move_task":
            task = board().move(int(args["id"]), args["status"])
            return f"Moved task #{task.id} to {task.status}", False
        if name == "board_stats":
            return json.dumps(board().stats()), False
        return f"Unknown tool: {name}", True
    except (KeyError, ValueError) as exc:
        return f"Error: {exc.args[0] if exc.args else exc}", True


def handle(msg: dict) -> dict | None:
    method, params, msg_id = msg.get("method"), msg.get("params") or {}, msg.get("id")
    if msg_id is None:  # a notification (e.g. notifications/initialized): never answered
        return None
    if method == "initialize":
        result = {
            "protocolVersion": params.get("protocolVersion") or FALLBACK_PROTOCOL,
            "capabilities": {"tools": {"listChanged": False}, "prompts": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": "Use these tools to read and change the taskboard instead of editing board.json.",
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        text, is_error = call_tool(params.get("name", ""), params.get("arguments") or {})
        result = {"content": [{"type": "text", "text": text}], "isError": is_error}
    elif method == "prompts/list":
        result = {"prompts": PROMPTS}
    elif method == "prompts/get" and params.get("name") == "standup":
        tasks = board().list()
        lines = "\n".join(f"- #{t.id} [{t.status}] {t.title}" for t in tasks) or "- (no tasks)"
        text = ("Write a three-line stand-up update (yesterday / today / blockers) from this board:\n" + lines)
        result = {"description": "Stand-up from the board",
                  "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}
    else:
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        else:
            log("→", msg)
            reply = handle(msg)
        if reply is not None:
            log("←", reply)
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
