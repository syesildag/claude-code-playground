"""Drive the MCP server over stdio exactly like Claude Code does: JSON-RPC, one message per line."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
APP = LAB.parents[1] / "app"


class McpServerTest(unittest.TestCase):
    def setUp(self) -> None:
        # Assemble a mini sandbox: the app plus the server, as ./lab new would.
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        (root / "mcp").mkdir()
        os.symlink(APP / "taskboard", root / "taskboard")
        server = root / "mcp" / "taskboard_server.py"
        server.write_text((LAB / "overlay" / "mcp" / "taskboard_server.py").read_text())
        env = {**os.environ, "TASKBOARD_DB": str(root / "board.json")}
        self.proc = subprocess.Popen([sys.executable, str(server)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     text=True, env=env)
        self.next_id = 0

    def tearDown(self) -> None:
        self.proc.stdin.close()
        self.proc.wait(timeout=5)
        self.proc.stdout.close()
        self._tmp.cleanup()

    def send(self, method: str, params: dict | None = None, notify: bool = False) -> dict | None:
        msg = {"jsonrpc": "2.0", "method": method, "params": params or {}}
        if not notify:
            self.next_id += 1
            msg["id"] = self.next_id
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        return None if notify else json.loads(self.proc.stdout.readline())

    def test_full_session(self) -> None:
        init = self.send("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                        "clientInfo": {"name": "test", "version": "0"}})
        self.assertEqual(init["result"]["protocolVersion"], "2025-11-25")
        self.assertIn("tools", init["result"]["capabilities"])
        self.send("notifications/initialized", notify=True)

        names = [t["name"] for t in self.send("tools/list")["result"]["tools"]]
        self.assertEqual(names, ["list_tasks", "add_task", "move_task", "board_stats"])

        added = self.send("tools/call", {"name": "add_task", "arguments": {"title": "write docs"}})["result"]
        self.assertFalse(added["isError"])
        self.assertIn("#1", added["content"][0]["text"])

        moved = self.send("tools/call", {"name": "move_task", "arguments": {"id": 1, "status": "doing"}})["result"]
        self.assertIn("doing", moved["content"][0]["text"])

        listing = self.send("tools/call", {"name": "list_tasks", "arguments": {}})["result"]
        self.assertIn("#1 [doing] write docs", listing["content"][0]["text"])

        prompt = self.send("prompts/get", {"name": "standup"})["result"]
        self.assertIn("write docs", prompt["messages"][0]["content"]["text"])

    def test_tool_errors_are_results_not_protocol_errors(self) -> None:
        self.send("initialize", {"protocolVersion": "2025-06-18"})
        result = self.send("tools/call", {"name": "move_task", "arguments": {"id": 99, "status": "done"}})
        self.assertTrue(result["result"]["isError"])
        self.assertIn("not found", result["result"]["content"][0]["text"])

    def test_unknown_method(self) -> None:
        self.assertEqual(self.send("resources/list")["error"]["code"], -32601)


if __name__ == "__main__":
    unittest.main()
