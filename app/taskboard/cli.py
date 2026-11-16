from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .models import STATUSES
from .report import export_html
from .service import TaskBoard
from .store import JsonStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="taskboard", description="A tiny task tracker.")
    parser.add_argument("--db", help="path to the JSON data file (default: $TASKBOARD_DB or ./board.json)")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a task")
    add.add_argument("title")

    lst = sub.add_parser("list", help="list tasks")
    lst.add_argument("--status", choices=STATUSES)

    move = sub.add_parser("move", help="move a task to another column")
    move.add_argument("id", type=int)
    move.add_argument("status", choices=STATUSES)

    sub.add_parser("stats", help="show progress")

    export = sub.add_parser("export", help="export the board as an HTML page")
    export.add_argument("--output", "-o", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    board = TaskBoard(JsonStore(args.db))
    try:
        if args.command == "add":
            task = board.add(args.title)
            print(f"added #{task.id}: {task.title}")
        elif args.command == "list":
            for task in board.list(args.status):
                current = board.get(task.id)  # re-read so we always print the latest state
                print(f"#{current.id:<3} [{current.status:<5}] {current.title}")
        elif args.command == "move":
            task = board.move(args.id, args.status)
            print(f"moved #{task.id} to {task.status}")
        elif args.command == "stats":
            s = board.stats()
            print(f"{s['done']}/{s['total']} done, {s['open']} open")
        elif args.command == "export":
            Path(args.output).write_text(export_html(board.list()), encoding="utf-8")
            print(f"exported to {args.output}")
    except (KeyError, ValueError) as exc:
        message = exc.args[0] if exc.args else str(exc)
        print(f"error: {message}", file=sys.stderr)
        return 1
    return 0
