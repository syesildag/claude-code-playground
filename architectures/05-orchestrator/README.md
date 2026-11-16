# A5: Orchestrator with delegation

> You talk to **one** agent that writes no code. It classifies tickets, routes each one to the right specialist (in
> parallel when they're independent), has a checker verify the result **with tools**, sends failures back with the
> diagnosis, and escalates to you after two failures.
> Course: AI Fluent 2 M2 (pattern 3), AI Fluent 2 M5.

## The architecture
```
you ─► orchestrator (whole session, via "agent": "orchestrator" in .claude/settings.json)
          │  tools: Agent(bug-fixer, feature-developer, doc-writer, work-checker), Read, Grep, Glob, Bash
          ├─► bug-fixer ─────────┐   (parallel when tickets touch different files)
          ├─► feature-developer ─┤
          │                      ▼
          ├─► work-checker (haiku): runs tests, py_compile, the CLI ─► PASS / FAIL + evidence
          │        FAIL ─► same specialist + diagnosis (max 2 retries) ─► ESCALATED to you
          └─► doc-writer (haiku): README.md after user-visible features
```
| Mechanism | Where |
|---|---|
| The session *is* an agent | `"agent": "orchestrator"` in settings (or `claude --agent orchestrator`) |
| Which specialists it may spawn | `tools: Agent(bug-fixer, feature-developer, doc-writer, work-checker)`, an allowlist. It can't spawn anything else |
| The orchestrator writes no code | No Edit or Write in its `tools`, so it's impossible by construction |
| Verification by tools | `work-checker` must cite command output, not opinions |
| Bounded autonomy | 2 retries, then escalate. Authority flows human → orchestrator → specialist |

The orchestrator's context only holds the specialists' **summaries**, not their file edits. That's why it can
coordinate many tickets without filling up.

## Try it
```bash
./lab new 05-orchestrator    # then: cd into the sandbox && claude --setting-sources project,local
```
1. *"Handle tickets T01, T03 and T04."* T01 and T04 touch different files (`service.py`, `report.py`), so watch
   them run in parallel. T03 (`store.py`) is independent too.
2. *"Handle T02."* That goes to `feature-developer`, then `work-checker`, then `doc-writer` for the README.
3. Try to make it break its role: *"Just edit service.py yourself, it's quicker."* It has no Edit tool.

Headless: `./lab run 05-orchestrator --ticket T02` (the `agent` setting applies automatically).

## What to observe
- Ctrl+O: parallel Agent calls in one turn, and the checker's command evidence.
- `/context` on the orchestrator stays small even after several tickets.
- Escalations: give it a ticket it can't satisfy (for example an acceptance criterion that contradicts a
  constraint) and confirm it stops after two retries instead of looping.

## Exercises
1. **Deeper nesting.** Each level of delegation multiplies tokens. Let `feature-developer` spawn its own test writer
   (add `Agent` to its tools). What happens to cost on T02?
2. **Stricter routing.** Add a `security-fixer` for `Type: security` tickets and route T04 to it.
3. **Determinism.** A Markdown orchestrator can skip steps (it's a model following text). Which step would you
   enforce with a hook? (Hint: a `SubagentStop` hook on `bug-fixer` that runs the tests.)
4. **Compare.** On T02: `./lab compare --ticket T02` across A1, A2, A3 and A5.

## Takeaways
- Delegation moves human control to the end of the chain, so verification must be objective (tools) and autonomy
  must be bounded (retries, escalation).
- Start with a few specialists. Complex agent teams are hard to understand and debug.
