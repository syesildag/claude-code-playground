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

    def test_ports_avoid_cockpit_default(self) -> None:
        self.assertIn(9190, lf.PORTS)
        self.assertNotIn(9090, lf.PORTS)

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


class TraceLookupTest(unittest.TestCase):
    def test_find_traces_polls_until_data(self) -> None:
        responses = iter([{"data": []}, {"data": [{"id": "t"}]}, {"data": [{"id": "t"}]}])
        calls = []

        def fake_api(env, method, path, body=None, base_url=lf.BASE_URL):
            calls.append(path)
            return next(responses)

        traces = lf.find_traces(lf.generate_env(), "sess-1", timeout=60, api=fake_api, sleep=lambda s: None)
        self.assertEqual(traces, [{"id": "t"}])
        self.assertEqual(len(calls), 3)  # empty, first data, same count again = stable
        # Langfuse v4 ("events_only" mode) only serves reads through the v2 observations API.
        self.assertTrue(calls[0].startswith("/api/public/v2/observations?"), calls[0])
        self.assertIn("sessionId=sess-1", calls[0])

    def test_find_traces_times_out_empty(self) -> None:
        empty = lambda env, method, path, body=None, base_url=lf.BASE_URL: {"data": []}  # noqa: E731
        self.assertEqual(lf.find_traces(lf.generate_env(), "s", timeout=0, api=empty, sleep=lambda s: None), [])

    def test_find_traces_survives_api_errors(self) -> None:
        def down(env, method, path, body=None, base_url=lf.BASE_URL):
            raise urllib.error.URLError("connection refused")

        self.assertEqual(lf.find_traces(lf.generate_env(), "s", timeout=0, api=down, sleep=lambda s: None), [])

    def test_find_traces_waits_until_count_is_stable(self) -> None:
        responses = iter([{"data": []}, {"data": [{"id": "a"}]}, {"data": [{"id": "a"}, {"id": "b"}]},
                          {"data": [{"id": "a"}, {"id": "b"}]}])
        fake_api = lambda env, method, path, body=None, base_url=lf.BASE_URL: next(responses)  # noqa: E731
        traces = lf.find_traces(lf.generate_env(), "s", timeout=60, api=fake_api, sleep=lambda s: None)
        self.assertEqual([t["id"] for t in traces], ["a", "b"])

    def test_find_traces_follows_cursor(self) -> None:
        calls = []

        def paged(env, method, path, body=None, base_url=lf.BASE_URL):
            calls.append(path)
            if "cursor=c2" in path:
                return {"data": [{"id": "b"}], "meta": {}}
            return {"data": [{"id": "a"}], "meta": {"cursor": "c2"}}

        traces = lf.find_traces(lf.generate_env(), "s", timeout=60, api=paged, sleep=lambda s: None)
        self.assertEqual([t["id"] for t in traces], ["a", "b"])
        self.assertTrue(any("cursor=c2" in c for c in calls))

    def test_count_traces_counts_distinct_trace_ids(self) -> None:
        observations = [{"id": "o1", "traceId": "t1"}, {"id": "o2", "traceId": "t1"}, {"id": "o3", "traceId": "t2"}]
        self.assertEqual(lf.count_traces(observations), 2)
        self.assertEqual(lf.count_traces([]), 0)

    def test_trace_warning_mentions_hook_log(self) -> None:
        message = lf.trace_warning("sess-9")
        self.assertIn("sess-9", message)
        self.assertIn(lf.HOOK_LOG, message)


class EnvSafetyTest(unittest.TestCase):
    def test_missing_env_with_existing_volumes_is_a_conflict(self) -> None:
        message = lf.env_volume_conflict(env_exists=False, volumes=["server_langfuse_postgres_data"])
        self.assertIn("down --wipe", message)

    def test_no_conflict_when_env_exists_or_no_volumes(self) -> None:
        self.assertIsNone(lf.env_volume_conflict(env_exists=True, volumes=["v"]))
        self.assertIsNone(lf.env_volume_conflict(env_exists=False, volumes=[]))

    def test_keys_ok(self) -> None:
        def unauthorized(env, method, path, body=None, base_url=lf.BASE_URL):
            raise urllib.error.HTTPError(lf.BASE_URL + path, 401, "Unauthorized", {}, None)

        self.assertFalse(lf.keys_ok(lf.generate_env(), api=unauthorized))
        self.assertTrue(lf.keys_ok(lf.generate_env(), api=lambda *a, **k: {"data": [{"id": "p"}]}))


if __name__ == "__main__":
    unittest.main()
