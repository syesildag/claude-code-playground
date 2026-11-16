---
name: tdd
description: Gated TDD workflow on a ticket. RED, GREEN, cold REVIEW and PROOF phases, with deterministic stop gates between them.
argument-hint: <ticket file, e.g. tickets/T02-add-priority.md>
disable-model-invocation: true
---

# Gated TDD on `$ARGUMENTS`

You are the orchestrator. You write no production code and no tests. Every phase ends at a **stop gate**: the
output of `scripts/gate.py`, never your own impression. "I ran the tests and they passed" is not a gate.

```
START ─► BASELINE ─► RED (tdd-red) ─gate─► GREEN (tdd-green) ─gate─► REVIEW (cold-reviewer) ─gate─► PROOF ─► CAPITALIZE ─► END
                      ▲                       │ fail, max 2               │ blocking, max 2 loops
                      └───────────────────────┴───────────────────────────┘
```

0. **Start.** `mkdir -p work/gates && touch work/.tdd-active`. From now on a Stop hook refuses to let the session
   end until `work/proof.html` exists.
1. **BASELINE.** `python3 scripts/gate.py baseline`
2. **RED.** Spawn `tdd-red` with the ticket path. Then run `python3 scripts/gate.py red`.
   On FAIL, give `tdd-red` the gate output (max 2 attempts). *Forbidden in this phase: production code changes.*
3. **GREEN.** Spawn `tdd-green` with the ticket path and the contents of `work/gates/red.txt`. Then run
   `python3 scripts/gate.py green`. On FAIL, give `tdd-green` the gate output (max 2 attempts).
   *Forbidden: editing the RED tests.*
4. **REVIEW.** Spawn `cold-reviewer` with **only** the ticket path. It reads the diff itself and writes
   `work/review.md`. Then run `python3 scripts/gate.py review`.
   On FAIL: a finding that needs a new test goes back to step 2; anything else goes to `tdd-green` with the findings.
   **After any fix, run the review again.** Max 2 loops.
5. **PROOF.** `python3 scripts/proof_page.py $ARGUMENTS`, which writes `work/proof.html`.
6. **CAPITALIZE.** Append one line per pitfall you hit to `docs/lessons.md` (`what happened → what to do next
   time`). Create the file if needed. If nothing went wrong, write that.
7. **END.** `rm work/.tdd-active`, then report `| gate | verdict |` and the path of the proof page.

## Known pitfalls (extend this list)
- Don't start the review before the GREEN gate has passed.
- Re-run the review after every fix. Don't assume the fix is right.
- Never report a gate as passed from memory: re-run `scripts/gate.py`.
