---
name: project-status
description: Summarize where the project stands right now (branch, uncommitted changes, recent commits, test results, open tickets). Use when the user asks for a status, "where are we", or what to do next.
allowed-tools: Bash(git branch *) Bash(git status *) Bash(git log *) Bash(python3 *)
---

# Project status

The lines below were filled in by shell commands **before** this prompt reached you (dynamic context injection).
Don't re-run them. Reason over the data.

- Branch: !`git branch --show-current`
- Uncommitted changes:
  !`git status --short`
- Recent commits:
  !`git log --oneline -5`
- Tests: !`python3 ${CLAUDE_SKILL_DIR}/scripts/test_summary.py`
- Open tickets: !`python3 ${CLAUDE_SKILL_DIR}/scripts/list_tickets.py`

Reply in at most 6 lines:
1. One line on the state of the code (clean or dirty, tests green or red).
2. The single most useful next action, and which ticket it serves.
