"""Offline tests for the --trace wiring in ./lab: no Claude, no Langfuse, no Docker."""

import importlib.machinery
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
_loader = importlib.machinery.SourceFileLoader("lab", str(REPO / "lab"))
_spec = importlib.util.spec_from_loader("lab", _loader)
lab = importlib.util.module_from_spec(_spec)
_loader.exec_module(lab)
lf = lab.lf


class TracingTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.sandbox = Path(self._tmp.name)
        self.settings = self.sandbox / ".claude" / "settings.local.json"
        self.settings.parent.mkdir()
        self.settings.write_text(json.dumps({"claudeMdExcludes": ["x"]}), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_apply_tracing_writes_env_and_returns_it(self) -> None:
        env = lf.generate_env()
        tags = lf.trace_tags("01-single-agent", "architecture")
        calls = []
        returned = lab.apply_tracing(self.sandbox, env, tags, enable=lambda sandbox: calls.append(sandbox) or "install")
        saved = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertEqual(calls, [self.sandbox])
        self.assertEqual(saved["claudeMdExcludes"], ["x"])
        self.assertEqual(saved["env"]["CC_LANGFUSE_TRACE_TAGS"], tags)
        self.assertEqual(saved["env"]["LANGFUSE_BASE_URL"], "http://localhost:3000")
        self.assertEqual(returned, saved["env"])

    def test_enable_plugin_uses_local_scope_install(self) -> None:
        seen = {}

        def ok_run(cmd, **kwargs):
            seen.update(cmd=cmd, cwd=kwargs.get("cwd"), stdin=kwargs.get("stdin"))
            return subprocess.CompletedProcess(cmd, 0, "{}", "")

        self.assertEqual(lab.enable_plugin(self.sandbox, run=ok_run), "install")
        self.assertEqual(seen["cmd"][1:], ["plugin", "install", lf.PLUGIN_ID, "--scope", "local", "--json"])
        self.assertEqual(seen["cwd"], self.sandbox)
        self.assertEqual(seen["stdin"], subprocess.DEVNULL)

    def test_enable_plugin_falls_back_to_settings(self) -> None:
        failing = lambda cmd, **kwargs: subprocess.CompletedProcess(cmd, 1, "", "nope")  # noqa: E731
        self.assertEqual(lab.enable_plugin(self.sandbox, run=failing), "settings")
        saved = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertIs(saved["enabledPlugins"][lf.PLUGIN_ID], True)
        self.assertEqual(saved["claudeMdExcludes"], ["x"])


if __name__ == "__main__":
    unittest.main()
