import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from taskboard.cli import main


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self._tmp.name) / "board.json")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cli(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--db", self.db, *args])
        return code, out.getvalue(), err.getvalue()

    def test_add_then_list(self) -> None:
        self.assertEqual(self.run_cli("add", "buy milk")[0], 0)
        code, out, _ = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertIn("buy milk", out)
        self.assertIn("[todo ]", out)

    def test_move_unknown_task_reports_error(self) -> None:
        code, _, err = self.run_cli("move", "9", "done")
        self.assertEqual(code, 1)
        self.assertIn("task 9 not found", err)

    def test_export_writes_html(self) -> None:
        self.run_cli("add", "ship it")
        target = Path(self._tmp.name) / "board.html"
        self.assertEqual(self.run_cli("export", "-o", str(target))[0], 0)
        self.assertIn("ship it", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
