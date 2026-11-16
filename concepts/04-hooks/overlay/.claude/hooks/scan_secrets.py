#!/usr/bin/env python3
"""Secret scanner used two ways: one script, two layers of defence.

1. Claude Code hook   PreToolUse(Bash) with "if": "Bash(git commit*)". It scans everything that could end up in
                      the commit (staged, unstaged and untracked files) and exits 2 to block.
2. git pre-commit     `python3 .claude/hooks/scan_secrets.py --git-hook`. Install it with
                      scripts/install-git-hook.sh. It scans only staged content and exits 1 to block.

The git hook can be skipped with `git commit --no-verify`, which is why block_dangerous_bash.py denies --no-verify.
The real last line of defence is the same scan in CI.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

PATTERNS = {
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "Anthropic API key": re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
    "hard-coded secret": re.compile(r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"),
}
FORBIDDEN_NAMES = re.compile(r"(^|/)(\.env(\.(?!example$)[^/]+)?|id_rsa|id_ed25519|[^/]+\.pem|[^/]+\.key)$")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def added_lines(diff: str) -> list[tuple[str, str]]:
    current, lines = "?", []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            lines.append((current, line[1:]))
    return lines


def scan(staged_only: bool) -> list[str]:
    findings: list[str] = []
    if staged_only:
        names = git("diff", "--cached", "--name-only").split()
        lines = added_lines(git("diff", "--cached"))
    else:
        untracked = git("ls-files", "--others", "--exclude-standard").split()
        names = git("diff", "HEAD", "--name-only").split() + git("diff", "--cached", "--name-only").split() + untracked
        lines = added_lines(git("diff", "HEAD")) + added_lines(git("diff", "--cached"))
        for name in untracked:
            path = Path(name)
            if path.is_file() and path.stat().st_size < 1_000_000:
                try:
                    lines += [(name, line) for line in path.read_text(encoding="utf-8").splitlines()]
                except UnicodeDecodeError:
                    pass
    for name in sorted(set(names)):
        if FORBIDDEN_NAMES.search(name):
            findings.append(f"{name}: this kind of file must never be committed")
    for name, line in lines:
        for label, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append(f"{name}: {label} ({line.strip()[:12]}…)")
    return sorted(set(findings))


def main() -> int:
    if "--git-hook" in sys.argv:
        findings = scan(staged_only=True)
        if findings:
            print("pre-commit: possible secrets, commit aborted:\n  " + "\n  ".join(findings), file=sys.stderr)
            return 1
        return 0

    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (event.get("tool_input") or {}).get("command", "")
    if "git commit" not in command:  # the "if" filter is best-effort, so check again
        return 0
    findings = scan(staged_only=False)
    if findings:
        print("scan_secrets.py blocked this commit. Possible secrets:\n  " + "\n  ".join(findings)
              + "\nRemove them (use environment variables) and make sure .env is gitignored.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
