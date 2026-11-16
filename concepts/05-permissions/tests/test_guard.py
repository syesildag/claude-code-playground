import json
import subprocess
import sys
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "overlay" / ".claude" / "hooks" / "guard_secret_reads.py"


def verdict(command: str) -> str:
    event = {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}}
    out = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event), text=True, capture_output=True).stdout
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else "none"


class GuardSecretReads(unittest.TestCase):
    def test_blocks_shell_reads_of_secrets(self) -> None:
        for command in ("cat .env", "python3 -c \"print(open('.env').read())\"", "grep -r token secrets/",
                        "cat ./.env.production", "head -1 secrets/prod-db.txt"):
            self.assertEqual(verdict(command), "deny", command)

    def test_allows_unrelated_commands(self) -> None:
        for command in ("python3 -m unittest", "cat .env.example", "git status", "ls taskboard/environment.py"):
            self.assertEqual(verdict(command), "none", command)


if __name__ == "__main__":
    unittest.main()
