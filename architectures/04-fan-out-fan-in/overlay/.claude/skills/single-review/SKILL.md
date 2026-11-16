---
name: single-review
description: Baseline for comparison. One agent reviews a path for bugs, security, performance and conventions all at once and writes work/review.md.
argument-hint: <path to review, default taskboard/>
disable-model-invocation: true
---

# Single-agent review of `$ARGUMENTS` (the baseline)

If no path was given, review `taskboard/`. Do the whole review yourself, with no subagents.

Cover four perspectives: functional bugs, security and data safety, performance, and the rules in
`docs/conventions.md`. Cite `file:line` for every finding.

Write `work/review.md`:
```
# Review: <target>
| # | Severity | Location | Issue | Fix |
|---|---|---|---|---|
```
Reply with the contents of `work/review.md`, nothing else.
