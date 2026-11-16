---
name: review
description: Review the current uncommitted changes with a five-point checklist (correctness, tests, security, conventions, scope) and give an APPROVE or REQUEST CHANGES verdict. Use when asked to review a diff or changes before committing.
allowed-tools: Bash(git diff *) Bash(git status *)
---

# Five-point review

1. Collect the change with `git status --porcelain` and `git diff HEAD`. If nothing changed, say so and stop.
2. For a second opinion from a fresh context, delegate to the `review-kit:reviewer` agent with the diff.
3. Check **correctness, tests, security, conventions, scope**, citing `file:line` for every finding.

Output a table `| # | Check | ✅/⚠️/❌ | Evidence |`, then **Verdict:** APPROVE or REQUEST CHANGES, with the one
reason that matters most.
