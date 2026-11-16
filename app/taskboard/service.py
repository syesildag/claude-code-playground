from __future__ import annotations

from datetime import datetime, timezone

from .models import STATUSES, Task
from .store import JsonStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class TaskBoard:
    """Business operations on top of a store. Every call reloads from disk, so the file is the truth."""

    def __init__(self, store: JsonStore) -> None:
        self.store = store

    def add(self, title: str) -> Task:
        title = title.strip()
        if not title:
            raise ValueError("title must not be empty")
        tasks = self.store.load()
        task = Task(id=max((t.id for t in tasks), default=0) + 1, title=title, created_at=_now())
        tasks.append(task)
        self.store.save(tasks)
        return task

    def get(self, task_id: int) -> Task:
        for task in self.store.load():
            if task.id == task_id:
                return task
        raise KeyError(f"task {task_id} not found")

    def move(self, task_id: int, status: str) -> Task:
        if status not in STATUSES:
            raise ValueError(f"unknown status {status!r}; expected one of: {', '.join(STATUSES)}")
        tasks = self.store.load()
        for task in tasks:
            if task.id == task_id:
                task.status = status
                self.store.save(tasks)
                return task
        raise KeyError(f"task {task_id} not found")

    def list(self, status: str | None = None) -> list[Task]:
        tasks = self.store.load()
        if status is not None:
            tasks = [t for t in tasks if t.status == status]
        return tasks

    def stats(self) -> dict[str, int]:
        tasks = self.store.load()
        done = sum(1 for t in tasks if t.status == "complete")
        return {"total": len(tasks), "done": done, "open": len(tasks) - done}
