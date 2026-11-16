"""The self-hosted Langfuse files: pinned upstream copy, localhost-only override, gitignored secrets."""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SERVER_DIR = REPO / "concepts" / "10-langfuse" / "server"


class ServerFilesTest(unittest.TestCase):
    def test_upstream_copy_is_pinned(self) -> None:
        head = "".join((SERVER_DIR / "docker-compose.yml").read_text(encoding="utf-8").splitlines(True)[:5])
        self.assertIn("https://github.com/langfuse/langfuse", head)
        self.assertIn("v4.80.0", head)

    def test_override_binds_public_ports_to_localhost(self) -> None:
        text = (SERVER_DIR / "docker-compose.lab.yml").read_text(encoding="utf-8")
        self.assertIn("!override", text)
        for binding in ("127.0.0.1:3000:3000", "127.0.0.1:3031:3031", "127.0.0.1:9090:9000"):
            self.assertIn(binding, text)

    def test_env_file_is_gitignored(self) -> None:
        proc = subprocess.run(["git", "check-ignore", "-q", "concepts/10-langfuse/server/.env"], cwd=REPO)
        self.assertEqual(proc.returncode, 0)

    @unittest.skipIf(shutil.which("docker") is None, "docker CLI not installed")
    def test_merged_config_has_no_public_bindings(self) -> None:
        proc = subprocess.run(
            ["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.lab.yml",
             "--env-file", ".env.example", "config", "--format", "json"],
            cwd=SERVER_DIR, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        services = json.loads(proc.stdout)["services"]
        bindings = [(name, port.get("host_ip"), port.get("published"))
                    for name, svc in services.items() for port in svc.get("ports", [])]
        self.assertTrue(bindings, "expected published ports")
        public = [b for b in bindings if b[1] != "127.0.0.1"]
        self.assertEqual(public, [], f"ports reachable from the network: {public}")


if __name__ == "__main__":
    unittest.main()
