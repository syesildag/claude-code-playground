# T01: Done counter always shows 0

**Type:** bug · **Size:** S

## Goal
`TaskBoard.stats()`, and therefore `taskboard stats`, must count the tasks whose status is `done`.
Today it reports `0/N done` even when tasks are in the done column.

## Context to read
- `taskboard/service.py`: `TaskBoard.stats()`
- `taskboard/models.py`: `STATUSES` is the single source of truth for status names
- `tests/test_service.py`: `test_stats_counts_done_tasks` currently fails

## Constraints
- Do not rename, add or remove statuses. `STATUSES` stays `("todo", "doing", "done")`.
- Do not modify existing tests to make them pass.
- Keep the return shape `{"total": int, "done": int, "open": int}`.

## Acceptance criteria
- [ ] With 3 tasks, 2 of them `done`, `stats()` returns `{"total": 3, "done": 2, "open": 1}`.
- [ ] With no tasks, `stats()` returns `{"total": 0, "done": 0, "open": 0}`.
- [ ] `python3 -m unittest` passes (every test, including the one that currently fails).

## Out of scope
- CLI output format, HTML export, persistence.
