"""Hidden acceptance checks for T03. Never copied into a sandbox before the agent has finished."""

import os
import tempfile
import unittest
from pathlib import Path

from taskboard import JsonStore, Task


class T03Acceptance(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.path = self.dir / "board.json"
        self.store = JsonStore(self.path)
        self.store.save([Task(1, "a"), Task(2, "b", status="done")])
        self.original = self.path.read_bytes()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _failing_save(self) -> None:
        # The second task holds a value JSON cannot encode: serialization fails partway through.
        self.store.save([Task(1, "a"), Task(2, object())])  # type: ignore[arg-type]

    def test_failed_save_keeps_previous_content(self) -> None:
        with self.assertRaises(Exception):
            self._failing_save()
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(len(JsonStore(self.path).load()), 2)

    def test_failed_save_leaves_no_temp_files(self) -> None:
        with self.assertRaises(Exception):
            self._failing_save()
        self.assertEqual(sorted(os.listdir(self.dir)), ["board.json"])

    def test_successful_save_leaves_only_board(self) -> None:
        self.store.save([Task(1, "a"), Task(2, "b"), Task(3, "c")])
        self.assertEqual(sorted(os.listdir(self.dir)), ["board.json"])
        self.assertEqual(len(self.store.load()), 3)
