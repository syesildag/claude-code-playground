---
paths:
  - "taskboard/cli.py"
---

# CLI rules

These load only when Claude works on `taskboard/cli.py`.

- Messages are lower-case and short: `added #3: buy milk`.
- Errors go to stderr as `error: <message>` and return exit code 1. Never print a traceback.
- Every sub-command has a `help=` text.
