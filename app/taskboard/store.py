from __future__ import annotations

import json
import os
from pathlib import Path

from .models import Task


def default_path() -> Path:
    return Path(os.environ.get("TASKBOARD_DB", "board.json"))


class JsonStore:
    """Persists tasks as a JSON array in a single file."""

    def __init__(self, path: str | os.PathLike | None = None) -> None:
        self.path = Path(path) if path is not None else default_path()

    def load(self) -> list[Task]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as fh:
            return [Task.from_dict(item) for item in json.load(fh)]

    def save(self, tasks: list[Task]) -> None:
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump([task.to_dict() for task in tasks], fh, indent=2)
