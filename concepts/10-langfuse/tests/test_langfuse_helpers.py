"""Offline tests for lablib/langfuse.py: no Docker, no network, no Langfuse server."""

import socket
import stat
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from lablib import langfuse as lf  # noqa: E402


class EnvTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / ".env"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_generate_env_keeps_shared_secrets_consistent(self) -> None:
        env = lf.generate_env()
        self.assertIn(f":{env['POSTGRES_PASSWORD']}@postgres:5432/", env["DATABASE_URL"])
        for key in ("LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY", "LANGFUSE_S3_MEDIA_UPLOAD_SECRET_ACCESS_KEY",
                    "LANGFUSE_S3_BATCH_EXPORT_SECRET_ACCESS_KEY"):
            self.assertEqual(env[key], env["MINIO_ROOT_PASSWORD"])
        self.assertEqual(len(env["ENCRYPTION_KEY"]), 64)
        self.assertTrue(env["LANGFUSE_INIT_PROJECT_PUBLIC_KEY"].startswith("pk-lf-"))
        self.assertTrue(env["LANGFUSE_INIT_PROJECT_SECRET_KEY"].startswith("sk-lf-"))
        self.assertEqual(env["LANGFUSE_IMAGE_TAG"], "4.80.0")
        self.assertEqual(env["TELEMETRY_ENABLED"], "false")

    def test_generate_env_values_are_random(self) -> None:
        self.assertNotEqual(lf.generate_env()["NEXTAUTH_SECRET"], lf.generate_env()["NEXTAUTH_SECRET"])

    def test_generate_env_covers_env_example(self) -> None:
        example = lf.read_env(lf.SERVER_DIR / ".env.example")
        self.assertEqual(set(example), set(lf.generate_env()))

    def test_write_env_is_private_and_round_trips(self) -> None:
        values = lf.generate_env()
        lf.write_env(self.path, values)
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.assertEqual(lf.read_env(self.path), values)

    def test_read_env_skips_comments_and_keeps_spaces(self) -> None:
        self.path.write_text("# comment\n\nA=1\nNAME=Claude Code Lab\n", encoding="utf-8")
        self.assertEqual(lf.read_env(self.path), {"A": "1", "NAME": "Claude Code Lab"})

    def test_ensure_env_is_idempotent(self) -> None:
        first, created_first = lf.ensure_env(self.path)
        second, created_second = lf.ensure_env(self.path)
        self.assertTrue(created_first)
        self.assertFalse(created_second)
        self.assertEqual(first, second)


class PluginWiringTest(unittest.TestCase):
    def test_trace_tags(self) -> None:
        self.assertEqual(lf.trace_tags("01-single-agent", "architecture", ticket="T01", model="haiku", run=2),
                         "lab:01-single-agent,kind:architecture,ticket:T01,model:haiku,run:2")
        self.assertEqual(lf.trace_tags("10-langfuse", "concept", ticket=None), "lab:10-langfuse,kind:concept")

    def test_plugin_env(self) -> None:
        env = lf.generate_env()
        out = lf.plugin_env(env, "lab:x,kind:concept")
        self.assertEqual(set(out), {"LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL",
                                    "LANGFUSE_USER_ID", "CC_LANGFUSE_TRACE_TAGS"})
        self.assertEqual(out["LANGFUSE_PUBLIC_KEY"], env["LANGFUSE_INIT_PROJECT_PUBLIC_KEY"])
        self.assertEqual(out["LANGFUSE_SECRET_KEY"], env["LANGFUSE_INIT_PROJECT_SECRET_KEY"])
        self.assertEqual(out["LANGFUSE_BASE_URL"], "http://localhost:3000")
        self.assertEqual(out["LANGFUSE_USER_ID"], "lab")
        self.assertEqual(out["CC_LANGFUSE_TRACE_TAGS"], "lab:x,kind:concept")

    def test_score_payloads(self) -> None:
        p = lf.score_payloads("sess-1", True, 0, "OK")
        self.assertEqual([s["name"] for s in p], ["accepted", "regressions"])
        self.assertEqual((p[0]["value"], p[0]["dataType"], p[0]["sessionId"]), (1, "BOOLEAN", "sess-1"))
        self.assertEqual(p[0]["comment"], "OK")
        self.assertEqual((p[1]["value"], p[1]["dataType"], p[1]["sessionId"]), (0, "NUMERIC", "sess-1"))
        self.assertEqual(lf.score_payloads("s", False, 3, "x")[0]["value"], 0)

    def test_session_url(self) -> None:
        env = lf.generate_env()
        self.assertEqual(lf.session_url(env, "sess-1"),
                         "http://localhost:3000/project/claude-code-lab/sessions/sess-1")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServiceTest(unittest.TestCase):
    def test_port_conflicts_detects_bound_port(self) -> None:
        holder = socket.socket()
        holder.bind(("127.0.0.1", 0))
        holder.listen()
        port = holder.getsockname()[1]
        try:
            self.assertEqual(lf.port_conflicts((port,)), [port])
        finally:
            holder.close()
        self.assertEqual(lf.port_conflicts((port,)), [])

    def test_docker_ok_false_for_missing_binary(self) -> None:
        self.assertFalse(lf.docker_ok("no-such-docker-xyz"))

    def test_healthy_false_when_nothing_listens(self) -> None:
        self.assertFalse(lf.healthy(f"http://127.0.0.1:{free_port()}", 0.5))

    def test_post_scores_returns_errors_instead_of_raising(self) -> None:
        def failing_api(env, method, path, body=None, base_url=lf.BASE_URL):
            raise urllib.error.URLError("connection refused")

        errors = lf.post_scores(lf.generate_env(), lf.score_payloads("s", True, 0, "OK"), api=failing_api)
        self.assertEqual(len(errors), 2)
        self.assertIn("connection refused", errors[0])


if __name__ == "__main__":
    unittest.main()
