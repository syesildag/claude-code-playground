"""Hidden acceptance checks for T01. Never copied into a sandbox before the agent has finished."""

import tempfile
import unittest
from pathlib import Path

from taskboard import STATUSES, JsonStore, TaskBoard


class T01Acceptance(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.board = TaskBoard(JsonStore(Path(self._tmp.name) / "board.json"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_counts_done_tasks(self) -> None:
        ids = [self.board.add(name).id for name in ("a", "b", "c")]
        self.board.move(ids[0], "done")
        self.board.move(ids[2], "done")
        self.assertEqual(self.board.stats(), {"total": 3, "done": 2, "open": 1})

    def test_empty_board(self) -> None:
        self.assertEqual(self.board.stats(), {"total": 0, "done": 0, "open": 0})

    def test_doing_is_not_done(self) -> None:
        task = self.board.add("a")
        self.board.move(task.id, "doing")
        self.assertEqual(self.board.stats()["done"], 0)

    def test_statuses_unchanged(self) -> None:
        self.assertEqual(STATUSES, ("todo", "doing", "done"))
