# Architecture

```
cli.py ──► service.py (TaskBoard) ──► store.py (JsonStore) ──► board.json
   │
   └──► report.py (export_html)
```

- `TaskBoard` holds no state. Every call reloads `board.json`, so hand edits are picked up right away.
- `JsonStore` is the only module that touches the filesystem.
- `report.py` renders HTML and must not import the store.
