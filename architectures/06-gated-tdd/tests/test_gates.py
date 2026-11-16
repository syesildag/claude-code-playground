"""Simulate a TDD cycle on a copy of the app and check that every gate gives the right verdict."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
APP = LAB.parents[1] / "app"
OVERLAY = LAB / "overlay"


class GatedTddTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "sandbox"
        shutil.copytree(APP, self.root, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(OVERLAY, self.root, dirs_exist_ok=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def gate(self, name: str) -> tuple[int, str]:
        proc = subprocess.run([sys.executable, "scripts/gate.py", name], cwd=self.root, capture_output=True,
                              text=True, timeout=300)
        return proc.returncode, proc.stdout

    def write(self, rel: str, text: str) -> None:
        (self.root / rel).write_text(textwrap.dedent(text), encoding="utf-8")

    def test_full_cycle(self) -> None:
        self.assertEqual(self.gate("baseline")[0], 0)
        self.assertEqual(self.gate("red")[0], 1, "RED must fail when no new test exists")

        self.write("tests/test_t01_red.py", """
            import tempfile, unittest
            from pathlib import Path
            class Red(unittest.TestCase):
                def test_two_done(self):
                    from taskboard import JsonStore, TaskBoard
                    with tempfile.TemporaryDirectory() as d:
                        b = TaskBoard(JsonStore(Path(d) / "b.json"))
                        for t in ("a", "b"):
                            b.move(b.add(t).id, "done")
                        self.assertEqual(b.stats()["done"], 2)
        """)
        code, out = self.gate("red")
        self.assertEqual(code, 0, out)
        self.assertIn("AssertionError", out)

        service = self.root / "taskboard" / "service.py"
        service.write_text(service.read_text().replace('"complete"', '"done"'))
        code, out = self.gate("green")
        self.assertEqual(code, 0, out)

        service.write_text(service.read_text().replace("title = title.strip()", "title = title"))
        self.assertEqual(self.gate("green")[0], 1, "a regression must fail GREEN")

    def test_red_rejects_module_import_errors(self) -> None:
        self.gate("baseline")
        self.write("tests/test_broken.py", """
            import unittest
            from taskboard.models import PRIORITIES  # not written yet: breaks the whole module
            class T(unittest.TestCase):
                def test_x(self): self.assertTrue(PRIORITIES)
        """)
        code, out = self.gate("red")
        self.assertEqual(code, 1)
        self.assertIn("failed to import", out)

    def test_review_gate(self) -> None:
        self.assertEqual(self.gate("review")[0], 1)
        (self.root / "work").mkdir(exist_ok=True)
        self.write("work/review.md", "VERDICT: PASS\n- [minor] a.py:1: naming → rename\n")
        self.assertEqual(self.gate("review")[0], 0)
        self.write("work/review.md", "VERDICT: FAIL\n- [blocking] store.py:9: not atomic → use os.replace\n")
        self.assertEqual(self.gate("review")[0], 1)

    def test_proof_page_escapes_html(self) -> None:
        (self.root / "work" / "gates").mkdir(parents=True)
        self.write("work/review.md", "VERDICT: PASS <script>alert(1)</script>\n")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        proc = subprocess.run([sys.executable, "scripts/proof_page.py"], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        html = (self.root / "work" / "proof.html").read_text()
        self.assertNotIn("<script>alert", html)
        self.assertIn("MISSING", html)


class RequireProofHook(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "work").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def stop(self, active: bool = False) -> dict:
        proc = subprocess.run([sys.executable, str(OVERLAY / ".claude/hooks/require_proof.py")],
                              input=json.dumps({"hook_event_name": "Stop", "stop_hook_active": active}),
                              text=True, capture_output=True, env={**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)})
        return json.loads(proc.stdout) if proc.stdout.strip() else {}

    def test_no_active_run_allows_stop(self) -> None:
        self.assertEqual(self.stop(), {})

    def test_active_run_without_proof_blocks(self) -> None:
        (self.root / "work/.tdd-active").touch()
        self.assertEqual(self.stop().get("decision"), "block")
        self.assertEqual(self.stop(active=True), {})

    def test_fresh_proof_allows_stop(self) -> None:
        (self.root / "work/.tdd-active").touch()
        time.sleep(0.02)
        (self.root / "work/proof.html").write_text("ok")
        self.assertEqual(self.stop(), {})


class ScopedWrites(unittest.TestCase):
    def check(self, path: str, *allowed: str) -> int:
        event = {"hook_event_name": "PreToolUse", "tool_name": "Write", "tool_input": {"file_path": path}}
        return subprocess.run([sys.executable, str(OVERLAY / ".claude/hooks/scoped_writes.py"), *allowed],
                              input=json.dumps(event), text=True, capture_output=True,
                              env={**os.environ, "CLAUDE_PROJECT_DIR": "/proj"}).returncode

    def test_scoping(self) -> None:
        self.assertEqual(self.check("/proj/tests/test_x.py", "tests/"), 0)
        self.assertEqual(self.check("/proj/taskboard/service.py", "tests/"), 2)
        self.assertEqual(self.check("work/plan.md", "work/"), 0)
        self.assertEqual(self.check("/proj/workaround.py", "work/"), 2, "prefix match must respect the slash")


if __name__ == "__main__":
    unittest.main()
