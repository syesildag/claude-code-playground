#!/usr/bin/env python3
"""Run Claude headlessly and print a live, human-readable trace of what the agent does.

A pocket-sized version of the LLMOps idea (AI Fluent 2 M7): turn "it feels slow" into "it re-read the same file
4 times". stream-json emits one event per line: system init, assistant messages (text, tool calls), tool results,
and a final result with cost and usage.

  python3 scripts/trace.py "Fix ticket tickets/T01-fix-done-counter.md" [--model haiku] [--budget 0.5]
"""

import argparse
import json
import subprocess
import sys
import time
from collections import Counter


def short(value: object, limit: int = 90) -> str:
    text = " ".join(str(value).split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt")
    parser.add_argument("--model", default="haiku")
    parser.add_argument("--budget", default="0.50")
    parser.add_argument("--mode", default="acceptEdits", help="permission mode for the run")
    args = parser.parse_args()

    # A new sandbox is an untrusted workspace, so allow rules in .claude/settings.json are ignored.
    # Rules passed with --settings still apply: let the agent run the tests.
    allow = {"permissions": {"allow": ["Bash(python3 -m unittest)", "Bash(python3 -m unittest *)"]}}
    cmd = ["claude", "-p", args.prompt, "--setting-sources", "project,local", "--settings", json.dumps(allow),
           "--model", args.model, "--output-format", "stream-json", "--verbose", "--permission-mode", args.mode,
           "--permission-prompts", "none", "--max-budget-usd", args.budget]
    started = time.time()
    tools: Counter = Counter()
    reads: Counter = Counter()
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True) as proc:
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = f"{time.time() - started:6.1f}s"
            kind = event.get("type")
            if kind == "system" and event.get("subtype") == "init":
                print(f"{t}  init   model={event.get('model')} tools={len(event.get('tools') or [])}")
            elif kind == "assistant":
                for block in event.get("message", {}).get("content", []):
                    if block.get("type") == "tool_use":
                        name, data = block.get("name"), block.get("input") or {}
                        tools[name] += 1
                        target = data.get("file_path") or data.get("command") or data.get("pattern") \
                            or data.get("description") or data
                        if name == "Read":
                            reads[data.get("file_path")] += 1
                        print(f"{t}  tool   {name:<8} {short(target)}")
                    elif block.get("type") == "text" and block.get("text", "").strip():
                        print(f"{t}  text   {short(block['text'])}")
            elif kind == "user":
                for block in event.get("message", {}).get("content", []) or []:
                    if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("is_error"):
                        print(f"{t}  error  {short(block.get('content'))}")
            elif kind == "result":
                usage = event.get("usage") or {}
                print(f"\n{t}  done   turns={event.get('num_turns')} cost=${event.get('total_cost_usd', 0):.4f} "
                      f"cache_read={usage.get('cache_read_input_tokens')} "
                      f"cache_write={usage.get('cache_creation_input_tokens')}")
    print("tool calls:", dict(tools))
    repeated = {f: n for f, n in reads.items() if n > 1}
    if repeated:
        print("files read more than once:", repeated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
