# Taskboard

A small Python task tracker (stdlib only, no dependencies).

- Run tests: `python3 -m unittest`
- Run the CLI: `python3 -m taskboard --help`
- Status names come from `STATUSES` in `taskboard/models.py`. Never hard-code them elsewhere.
- Work items live in `tickets/`. Each one has acceptance criteria. Meet all of them before you finish.
