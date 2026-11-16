import tempfile
import unittest
from pathlib import Path

from taskboard import JsonStore, Task


class JsonStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "board.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_missing_file_loads_as_empty_board(self) -> None:
        self.assertEqual(JsonStore(self.path).load(), [])

    def test_round_trip(self) -> None:
        tasks = [Task(1, "a"), Task(2, "b", status="done")]
        JsonStore(self.path).save(tasks)
        self.assertEqual(JsonStore(self.path).load(), tasks)


if __name__ == "__main__":
    unittest.main()
