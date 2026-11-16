# Taskboard

A tiny command-line task tracker. Tasks move through three columns: todo, doing, done.

```bash
python3 -m taskboard add "write the release notes"
python3 -m taskboard move 1 doing
python3 -m taskboard list
python3 -m taskboard stats
python3 -m taskboard export -o board.html
```

Data is stored in `board.json` in the current directory, or in the file named by `$TASKBOARD_DB` or `--db`.

Run the tests with `python3 -m unittest`.
