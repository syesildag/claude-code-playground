# T02: Tasks have a priority

**Type:** feature · **Size:** M

## Goal
Each task has a priority (`low`, `medium` or `high`), and the board can be listed in priority order.

## Context to read
- `taskboard/models.py`: `Task`, `STATUSES`
- `taskboard/service.py`: `TaskBoard.add()`, `TaskBoard.list()`
- `taskboard/cli.py`: the `add` and `list` sub-commands
- `taskboard/store.py`: how tasks are loaded from JSON

## Constraints
- Define `PRIORITIES = ("low", "medium", "high")` in `taskboard/models.py` and use it everywhere. Don't hard-code the names.
- Existing callers must keep working: `add(title)` and `list(status)` (positional) keep their meaning.
- Existing `board.json` files must keep loading. Users already have data.
- Stdlib only.

## Acceptance criteria
- [ ] `Task` has a `priority` attribute that defaults to `"medium"`, and it is persisted in `board.json`.
- [ ] `TaskBoard.add(title, priority="high")` stores the priority. Any value outside `PRIORITIES` raises `ValueError`.
- [ ] A `board.json` written before this change (tasks without a `priority` key) loads without error, and those tasks get priority `"medium"`.
- [ ] `TaskBoard.list(order="priority")` returns high, then medium, then low. Ties are broken by ascending id.
- [ ] `TaskBoard.list()` with no arguments still returns tasks in id order.
- [ ] `status` and `order` can be combined: `list("todo", order="priority")`.
- [ ] CLI: `python3 -m taskboard add "x" --priority high` and `python3 -m taskboard list --order priority` work.
- [ ] New behaviour is covered by tests, and `python3 -m unittest` passes.

## Out of scope
- Changing the priority of an existing task (no `set-priority` command).
- Showing priority in the HTML export.
