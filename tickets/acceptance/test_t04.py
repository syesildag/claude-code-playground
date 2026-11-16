"""Hidden acceptance checks for T04. Never copied into a sandbox before the agent has finished."""

import unittest

from taskboard import Task
from taskboard.report import export_html


class T04Acceptance(unittest.TestCase):
    def test_script_tag_is_escaped(self) -> None:
        html = export_html([Task(1, "<script>alert(1)</script>")])
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)

    def test_ampersand_and_quotes_escaped(self) -> None:
        html = export_html([Task(1, 'Tom & "Jerry"')])
        self.assertIn("Tom &amp; &quot;Jerry&quot;", html)

    def test_page_title_escaped(self) -> None:
        html = export_html([], title="<b>board</b>")
        self.assertNotIn("<b>board</b>", html)
        self.assertIn("&lt;b&gt;board&lt;/b&gt;", html)

    def test_structure_kept(self) -> None:
        html = export_html([Task(1, "a"), Task(2, "b", status="done")])
        self.assertEqual(html.count("<li"), 2)
        self.assertIn('class="done"', html)
