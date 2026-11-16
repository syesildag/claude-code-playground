---
name: pev
description: Run the Planner → Executor → Verifier workflow on a ticket, with deterministic gates before the independent verification.
argument-hint: <ticket file, e.g. tickets/T02-add-priority.md>
disable-model-invocation: true
---

# Planner → Executor → Verifier on `$ARGUMENTS`

You are the **coordinator**. You don't write code. You route work between three roles and enforce the gates.

```
PLAN (planner/opus) ─► EXECUTE (executor/sonnet) ─► GATES (you: tests) ─► VERIFY (verifier, fresh context)
                            ▲                            │ red                     │ FAIL
                            └────────────────────────────┴─────────────────────────┘   at most 2 retry rounds
```

1. **Plan.** Spawn the `planner` agent with the ticket path.
   *Gate:* `work/plan.md` exists and has a `## Definition of Done` section. If not, ask the planner once more,
   then stop.
2. **Execute.** Spawn the `executor` agent: "Implement work/plan.md for ticket `$ARGUMENTS`."
3. **Deterministic gates (you, cheap and first).** Run `python3 -m unittest -q`. A test that was already failing
   before you started is acceptable only if the ticket doesn't touch it. If anything new is red, send the output to
   `executor` and count one retry round.
4. **Verify.** Collect `git diff HEAD` plus the content of new files (`git status --porcelain`). Spawn the
   `verifier` agent with **only**: the diff, the ticket's "Acceptance criteria" section, and
   `docs/definition-of-done.md`. Do **not** pass the plan, your reasoning or the executor's summary. Independence is
   the point.
5. **Loop.** If the verifier returns `VERDICT: FAIL`, send its findings to `executor` and repeat steps 3–4. After 2
   retry rounds, stop and hand over to the human with the open findings.
6. **Report** as a table: `| phase | agent | result |`, then the final verdict and the last line of the test run.
