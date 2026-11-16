# Package notes (nested CLAUDE.md)

This file loads only when Claude reads or edits a file inside `taskboard/`.

- `TaskBoard` deliberately reloads from disk on every call. Don't add caching: hand edits to `board.json` must show
  up right away.
- Keep `service.py` free of I/O other than through `JsonStore`.
