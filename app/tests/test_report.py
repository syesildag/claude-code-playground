import unittest

from taskboard import Task
from taskboard.report import count_by_status, export_html


class ReportTest(unittest.TestCase):
    def test_export_lists_every_task_with_its_status(self) -> None:
        html = export_html([Task(1, "write docs"), Task(2, "fix bug", status="done")])
        self.assertIn("#1 write docs", html)
        self.assertIn('class="done"', html)

    def test_count_by_status(self) -> None:
        tasks = [Task(1, "a"), Task(2, "b", status="done"), Task(3, "c", status="done")]
        self.assertEqual(count_by_status(tasks), {"todo": 1, "done": 2})


if __name__ == "__main__":
    unittest.main()
