---
name: taskboard-domain
description: Domain rules of the taskboard (status lifecycle, what "open" and "done" mean, how ids are assigned). Use when changing task statuses, stats, ids, or any code that interprets a task's state.
user-invocable: false
paths:
  - "taskboard/**"
  - "tests/**"
---

# Taskboard domain rules

- Lifecycle: `todo` → `doing` → `done`. Moving backwards is allowed (re-opening a task).
- "Open" means not done: `todo` plus `doing`.
- Ids are never reused. The next id is the highest existing id plus one.
- Status names exist only in `STATUSES` (`taskboard/models.py`). Compare against that tuple. A string literal like
  `"complete"` in business code is a bug waiting to happen.
- `stats()` returns exactly `{"total", "done", "open"}` with `open == total - done`.
