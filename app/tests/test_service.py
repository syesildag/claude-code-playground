import tempfile
import unittest
from pathlib import Path

from taskboard import JsonStore, TaskBoard


class TaskBoardTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.board = TaskBoard(JsonStore(Path(self._tmp.name) / "board.json"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_add_assigns_incrementing_ids(self) -> None:
        first = self.board.add("write tests")
        second = self.board.add("ship it")
        self.assertEqual((first.id, second.id), (1, 2))

    def test_add_strips_title_and_rejects_blank(self) -> None:
        self.assertEqual(self.board.add("  tidy  ").title, "tidy")
        with self.assertRaises(ValueError):
            self.board.add("   ")

    def test_move_changes_status(self) -> None:
        task = self.board.add("review PR")
        self.board.move(task.id, "doing")
        self.assertEqual(self.board.get(task.id).status, "doing")

    def test_move_rejects_unknown_status(self) -> None:
        task = self.board.add("review PR")
        with self.assertRaises(ValueError):
            self.board.move(task.id, "archived")

    def test_move_unknown_task_raises_key_error(self) -> None:
        with self.assertRaises(KeyError):
            self.board.move(42, "done")

    def test_list_filters_by_status(self) -> None:
        a = self.board.add("a")
        self.board.add("b")
        self.board.move(a.id, "doing")
        self.assertEqual([t.title for t in self.board.list("doing")], ["a"])
        self.assertEqual(len(self.board.list()), 2)

    def test_stats_counts_done_tasks(self) -> None:
        a = self.board.add("a")
        self.board.add("b")
        self.board.move(a.id, "done")
        self.assertEqual(self.board.stats(), {"total": 2, "done": 1, "open": 1})


if __name__ == "__main__":
    unittest.main()
