"""Hidden acceptance checks for T02. Never copied into a sandbox before the agent has finished."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from taskboard import JsonStore, TaskBoard
from taskboard.cli import main


class T02Acceptance(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "board.json"
        self.board = TaskBoard(JsonStore(self.path))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_priorities_constant(self) -> None:
        from taskboard.models import PRIORITIES

        self.assertEqual(tuple(PRIORITIES), ("low", "medium", "high"))

    def test_default_priority_is_medium_and_persisted(self) -> None:
        task = self.board.add("a")
        self.assertEqual(self.board.get(task.id).priority, "medium")
        self.assertEqual(json.loads(self.path.read_text())[0]["priority"], "medium")

    def test_invalid_priority_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.board.add("x", priority="urgent")

    def test_order_by_priority_then_id(self) -> None:
        self.board.add("a", priority="low")
        self.board.add("b", priority="high")
        self.board.add("c")
        self.board.add("d", priority="high")
        self.assertEqual([t.title for t in self.board.list(order="priority")], ["b", "d", "c", "a"])

    def test_default_list_order_is_by_id(self) -> None:
        self.board.add("a", priority="low")
        self.board.add("b", priority="high")
        self.assertEqual([t.title for t in self.board.list()], ["a", "b"])

    def test_status_and_order_combine(self) -> None:
        a = self.board.add("a", priority="low")
        self.board.add("b", priority="high")
        self.board.add("c", priority="medium")
        self.board.move(a.id, "done")
        self.assertEqual([t.title for t in self.board.list("todo", order="priority")], ["b", "c"])

    def test_legacy_file_without_priority_loads(self) -> None:
        legacy = [{"id": 1, "title": "old", "status": "todo", "created_at": ""}]
        self.path.write_text(json.dumps(legacy), encoding="utf-8")
        self.assertEqual(self.board.get(1).priority, "medium")

    def test_cli_add_with_priority_and_list_order(self) -> None:
        def run(*args: str) -> tuple[int, str]:
            out = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
                code = main(["--db", str(self.path), *args])
            return code, out.getvalue()

        self.assertEqual(run("add", "low one", "--priority", "low")[0], 0)
        self.assertEqual(run("add", "urgent one", "--priority", "high")[0], 0)
        code, out = run("list", "--order", "priority")
        self.assertEqual(code, 0)
        self.assertLess(out.index("urgent one"), out.index("low one"))
