# A2: Planner / Executor / Verifier

> The question isn't "how many agents?" but **who produces, who validates, and who decides?** The agent that
> produces the work must never be the one that validates it.
> Course: AI Fluent 2 M1, AI Foundation M3, AI Fluent 1 M3 ("invert the effort").

## The architecture
```
 you ─/pev T02─► coordinator (main thread: routes and enforces gates, writes no code)
                    │
                    ├─1─► planner   (opus, Read/Grep/Glob + Write limited to work/ by a hook) ──► work/plan.md + Definition of Done
                    ├─2─► executor  (sonnet, full edit + Bash)  ─ implements the plan step by step, tests after each step
                    ├─3─► GATES     (coordinator runs python3 -m unittest: deterministic, cheap, FIRST)
                    └─4─► verifier  (sonnet, read-only, FRESH context: gets only diff + acceptance criteria + DoD) ──► PASS / FAIL
                              FAIL ──► back to executor with findings (at most 2 rounds) ──► then a human
```

| Design choice | Why (course) |
|---|---|
| The planner uses the strongest model | "Invert the effort": spend on planning so implementation succeeds the first time |
| The planner can only write `work/` | Separation of powers, enforced by a frontmatter hook (`scoped_writes.py`), not by politeness |
| Deterministic gates before the verifier | A test run costs nothing compared with an LLM verification. Don't pay for a review of red code |
| The verifier gets the diff, not the reasoning | A verifier who reads the author's reasoning inherits their blind spots. Independence comes from context |
| Retries are bounded | A loop without a cap burns tokens. Escalate to a human |

## What's in this lab
`.claude/agents/{planner,executor,verifier}.md`, `.claude/skills/pev/SKILL.md` (the workflow),
`.claude/hooks/scoped_writes.py`, and `docs/definition-of-done.md` (the non-functional criteria the planner copies
into every plan).

## Try it
```bash
./lab new 02-planner-executor-verifier    # then: cd into the sandbox && claude --setting-sources project,local
```
`/pev tickets/T03-atomic-save.md`, then read `work/plan.md` and the verifier's verdict.

As an experiment against the control group:
```bash
./lab run 02-planner-executor-verifier --ticket T03
./lab run 01-single-agent --ticket T03
./lab compare --ticket T03
```
The `cost by model` line shows the routing at work. Expect most of the money on Opus planning, not on execution.

## What to observe
- Ctrl+O: three separate subagent transcripts. The verifier never sees the plan.
- Did the verifier catch anything the gates missed? On T03 the classic miss is temp files left behind after a
  failed save. On T04 it's the unescaped page `title`.
- Did the planner try to edit code? Check the transcript for a `scoped_writes.py` denial.

## Exercises
1. **Different model family.** The course team plans with Opus, executes with Sonnet and reviews with *another
   vendor's* model to avoid shared blind spots. The closest you can get here is `verifier: model: opus` or `haiku`.
   Does verdict quality change?
2. **Remove independence.** Change step 4 of the skill so the verifier also receives `work/plan.md`. Is it more
   lenient?
3. **Split the verifier** into security and correctness verifiers run in parallel (see A4).
4. **Cost check.** Is this architecture worth it on T01 (a one-line fix)? On T02? Use `./lab compare`.

## Takeaways
- Reliability comes from how the work is split up, not from the number of agents.
- Gates decide. LLM verifiers signal. Run the deterministic ones first.
