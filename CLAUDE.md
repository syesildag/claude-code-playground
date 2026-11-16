# Claude Code Lab: authoring guide

This repo is a playground for Claude Code concepts and a testbed for agent architectures. You are probably here to
**add or improve a lab**. Labs run in sandboxes built by `./lab`; this file is excluded from those sandboxes.

## Layout
- `app/`: the practice app (Python stdlib "taskboard") copied into every sandbox. Its bugs are **deliberate**:
  the `stats()` status typo (T01), the unescaped HTML export (T04), the non-atomic save (T03), the extra reload
  in `cli list`. Never fix them in `app/`. Tickets and labs depend on them.
- `tickets/`: AI-ready work items. `acceptance/` holds hidden tests and `reference/` holds known-good patches.
- `concepts/NN-topic/`, `architectures/NN-pattern/`: one lab each: `lab.json`, `README.md`, `overlay/`
  (files copied on top of the app in the sandbox), optional `tests/` (run by `./lab check`).
- `templates/lab/`: skeleton used by `./lab scaffold`.

## Commands
- `./lab check`: run after every change. It validates JSON, compiles Python, runs lab tests, runs
  `claude plugin validate`, and proves each hidden test fails on the baseline and passes with its reference patch.
- `./lab new <lab>` builds a sandbox. `./lab inspect <lab>` shows what a session loads (one small Haiku call).

## Conventions for lab content
- Python 3 stdlib only. Hook scripts read JSON on stdin and must never crash on unexpected input.
- Reference hook scripts as `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/<name>.py"`.
- Skill descriptions say what the skill does **and when to use it**. They are activation conditions, not docs.
- Every agent declares `tools` (least privilege) and `model` (routing is part of the architecture).
- Lab READMEs follow `templates/lab/README.md`: concept, what's in the lab, try it, what to observe, exercises.
- Write in plain, direct English. Prefer a table or a numbered list to long prose.
