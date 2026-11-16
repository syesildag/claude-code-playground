from __future__ import annotations

from dataclasses import asdict, dataclass

# The board's columns, in display order. This tuple is the single source of truth for status names.
STATUSES: tuple[str, ...] = ("todo", "doing", "done")


@dataclass
class Task:
    id: int
    title: str
    status: str = "todo"
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Task:
        return cls(**data)
