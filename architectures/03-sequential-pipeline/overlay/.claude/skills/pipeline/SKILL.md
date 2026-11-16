---
name: pipeline
description: Run the sequential pipeline spec-writer → developer → test-writer on a ticket, with a human checkpoint after the spec.
argument-hint: <ticket file> [--auto]
disable-model-invocation: true
---

# Sequential pipeline on `$ARGUMENTS`

You coordinate. You never write code or tests yourself. Each stage's **artifact** is the next stage's only input.

```
ticket ─► spec-writer ─► work/spec.md ─► [human checkpoint] ─► developer ─► taskboard/ ─► test-writer ─► tests/ ─► report
```

1. **Spec.** Spawn `spec-writer` with the ticket path.
   *Gate:* `work/spec.md` exists and contains `Given`.
2. **Human checkpoint.** Unless the arguments contain `--auto`, show the user the Behaviour lines from the spec and
   ask: "Approve this spec? (yes / changes)". Wait for the answer. If they want changes, send them to `spec-writer`
   and repeat.
3. **Develop.** Spawn `developer`: "Implement work/spec.md." If it replies `NO SPEC`, stop and report that.
4. **Test.** Spawn `test-writer`: "Write tests for work/spec.md."
5. **Fix loop.** If the test writer reports a failing test caused by the code, send that report to `developer` once,
   then let `test-writer` rerun the suite. Then stop, whatever the result.
6. **Report:** `| stage | agent | artifact | result |`, plus the last line of `python3 -m unittest -q`.
