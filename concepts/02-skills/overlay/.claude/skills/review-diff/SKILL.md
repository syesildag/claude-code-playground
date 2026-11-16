---
name: review-diff
description: Review the current uncommitted changes against a five-point checklist (correctness, tests, security, conventions, scope) and give an APPROVE or REQUEST CHANGES verdict. Use when the user asks to review a diff, review changes, or check work before committing.
allowed-tools: Bash(git diff *) Bash(git status *) Bash(python3 -m unittest *)
---

# Review the diff

1. Collect the change with `git status --porcelain` and `git diff HEAD`. Read untracked files in full.
   If nothing changed, say so and stop.
2. Run `python3 -m unittest -q` once and note the result line.
3. Check each point and cite evidence as `file:line`:
   1. **Correctness**: does the code do what the change intends? Look for edge cases (empty input, missing file).
   2. **Tests**: is the new behaviour covered? Were existing tests weakened or edited to pass?
   3. **Security**: unescaped output, unsafe file writes, secrets, `eval`/`pickle`/`shell=True`.
   4. **Conventions**: status names only from `STATUSES`, stdlib only, errors to stderr.
   5. **Scope**: anything changed that the task didn't ask for?

## Output format

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Correctness | ✅ / ⚠️ / ❌ | `file:line`: one line |

**Verdict:** APPROVE or REQUEST CHANGES, with the one reason that matters most.
