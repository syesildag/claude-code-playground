# Taskboard

Small Python task tracker, stdlib only.

## Commands
- Test: `python3 -m unittest`. It takes under a second, so run it after every change.
- CLI: `python3 -m taskboard --help`

## Rules the code can't tell you
- Status names come only from `STATUSES` in `taskboard/models.py`. Never hard-code them elsewhere.
- Never edit an existing test to make it pass. Fix the code, or explain why the test is wrong.
- Keep `board.json` human-readable (indented JSON): users edit it by hand.

## Where to look
- Architecture overview (always loaded): @docs/architecture.md
- Before you use domain terms (status names, "board", "column"), read `docs/glossary.md`.

## Canary
End every final answer with the word `pygmalion` on its own line.
