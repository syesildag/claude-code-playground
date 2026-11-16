# A6: Gated TDD workflow

> Even with good agents, a human usually triggers each step ("now plan, now test, now code…"). Here a Markdown
> orchestrator chains RED → GREEN → REVIEW → PROOF by itself. Between phases it must pass **stop gates**:
> observable, deterministic evidence produced by a script, never the model's say-so.
> Course: AI Fluent 2 M5 (orchestrator agents), AI Fluent 1 M7 (quality control, proof).

## The architecture
```
/tdd T02 ─► BASELINE ─► RED (tdd-red, haiku) ─gate─► GREEN (tdd-green, sonnet) ─gate─► REVIEW (cold-reviewer, opus) ─gate─► PROOF ─► CAPITALIZE
                        ▲  writes tests/ only        │ writes taskboard/ only        │ read-only + work/review.md
                        └────────────────────────────┴───────────────────────────────┘  fail → loop back (max 2)
```
| Gate (`scripts/gate.py`) | Passes when |
|---|---|
| `baseline` | Always. Records which tests already fail (the T01 test), so later gates aren't fooled by them |
| `red` | ≥ 1 **new** failing test, and no test module failed to import (a syntax error is not "red for the right reason") |
| `green` | Every RED test passes, and nothing that passed at baseline fails now |
| `review` | `work/review.md` has a `VERDICT:` line and no `[blocking]` finding |

The other guards are deterministic too:
- **Scoped writes:** RED can only write `tests/`, GREEN only `taskboard/`, the reviewer only `work/` (frontmatter hooks).
- **Stop hook** `require_proof.py`: while `work/.tdd-active` exists, the session can't end without a fresh
  `work/proof.html`. The course demo forgot the proof page after its context degraded. Here that can't happen.
- **Capitalization:** each run appends its pitfalls to `docs/lessons.md`, so the workflow improves over time.

## Try it
```bash
./lab new 06-gated-tdd    # then: cd into the sandbox && claude --setting-sources project,local
```
1. `/tdd tickets/T02-add-priority.md`
2. Watch `work/gates/*.txt` appear, then open `work/proof.html` in a browser.
3. Read `docs/lessons.md`. What did the run learn?

Headless: `./lab run 06-gated-tdd --ticket T02` (Opus review: expect it to cost more than A1. Compare acceptance.)

## What to observe
- The gate files are the proof: `cat work/gates/red.txt` shows *why* each new test failed
  (`FAIL test_x → AssertionError: …`).
- Ctrl+O: a phase that fails its gate goes back with the gate output, not with the orchestrator's interpretation.
- The orchestrator's context stays small. It sees conclusions and gate output, not exploration noise.

## Exercises
1. **Break a gate on purpose.** In RED, ask `tdd-red` to import `PRIORITIES` at module level. The gate rejects it.
   Why does that rule exist?
2. **Model per phase.** Swap `cold-reviewer` to `sonnet` and `tdd-red` to `sonnet`. Does acceptance on T02 change?
   Does cost? (`./lab compare --ticket T02`)
3. **Find the skipped step.** The course's own demo found that the orchestrator didn't re-run the review after a
   fix. Our skill says to. Check the transcript: did it? If you can't rely on that, how would you make it a gate?
4. **Real determinism.** A Markdown workflow reaches maybe 99% reliability, not 100%. Ask Claude to generate a
   Claude Agent SDK (or LangGraph) version of this workflow, using `SKILL.md` as the spec.

## Takeaways
- Write the workflow as text, but enforce what matters with scripts and hooks.
- Read the proofs. Don't take the agent's word for it.
- You become the designer of the orchestration and the guardian of its gates.
