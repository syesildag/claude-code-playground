#!/usr/bin/env python3
"""Status line: Claude Code pipes session JSON to this script on stdin and shows whatever it prints.

Example output:  Haiku │ 01-claude-md │ ⎇ main* │ ctx ▓▓░░░░░░░░ 18% │ $0.042
"""

import json
import os
import subprocess
import sys


def git_branch(cwd: str) -> str:
    try:
        branch = subprocess.run(["git", "branch", "--show-current"], cwd=cwd, capture_output=True,
                                text=True, timeout=2).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=cwd, capture_output=True,
                               text=True, timeout=2).stdout.strip()
        return f"⎇ {branch}{'*' if dirty else ''}" if branch else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("statusline: no data")
        return
    model = (data.get("model") or {}).get("display_name", "?")
    workspace = data.get("workspace") or {}
    cwd = workspace.get("current_dir") or data.get("cwd") or "."
    window = data.get("context_window") or {}
    pct = window.get("used_percentage") or 0
    bar = "▓" * round(pct / 10) + "░" * (10 - round(pct / 10))
    cost = (data.get("cost") or {}).get("total_cost_usd")
    style = (data.get("output_style") or {}).get("name", "")
    parts = [model, os.path.basename(cwd), git_branch(cwd), f"ctx {bar} {pct:.0f}%"]
    if isinstance(cost, (int, float)):
        parts.append(f"${cost:.3f}")
    if style and style != "default":
        parts.append(f"style: {style}")
    print(" │ ".join(p for p in parts if p))


if __name__ == "__main__":
    main()
