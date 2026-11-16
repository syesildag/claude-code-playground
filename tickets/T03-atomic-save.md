# T03: Saving must never corrupt the board

**Type:** reliability · **Size:** S

## Goal
A failure while saving (an exception during serialization, a crash halfway through a write) must never
truncate or corrupt the existing `board.json`. Users have lost their whole board this way.

## Context to read
- `taskboard/store.py`: `JsonStore.save()`

## Constraints
- Public API unchanged: `JsonStore(path)`, `.load()`, `.save(tasks)`.
- Stdlib only. Must work on POSIX and Windows (hint: `os.replace`).
- The exception that caused the failure must still reach the caller. Don't swallow errors.

## Acceptance criteria
- [ ] If serialization fails partway through (for example, a task holds a value JSON can't encode), the previous contents of `board.json` are byte-for-byte unchanged.
- [ ] The original exception propagates out of `save()`.
- [ ] After a failed save, no temporary files are left next to `board.json`.
- [ ] After a successful save, the directory holds only `board.json`.
- [ ] `python3 -m unittest` passes, and a regression test covers the failure case.

## Out of scope
- Locking between concurrent processes.
