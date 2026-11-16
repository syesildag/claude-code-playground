# 01: CLAUDE.md & context engineering

> Claude has no memory between sessions ("Memento"). Instruction files are its tattoos. This lab shows **when each
> file enters the context**, what belongs in it, and what happens when it lies.
> Course: AI Foundation M1–M2, AI Fluent 1 M1–M2, M7 (canary).

## The concept
- `CLAUDE.md` files load from the working directory **and every parent directory**, concatenated, not overridden.
  When two files contradict each other, Claude may pick either one, silently.
- `@path` imports are **eager**: the imported file loads at launch with its parent. They help humans organize text,
  but they don't save tokens.
- A **nested** `sub/CLAUDE.md` and **path-scoped rules** (`.claude/rules/*.md` with `paths:`) are **lazy**: they
  load only once Claude touches a matching file.
- Mentioning a file in backticks instead of importing it is **progressive disclosure**: Claude reads it only if it
  decides to.
- `AGENTS.md` (the cross-tool standard) is read by Claude Code **only when there is no CLAUDE.md** in this directory
  or above it (v2.1.277+). The course notes predate this: they say Claude Code never reads it.
- Put in what the code can't tell the agent: pitfalls, conventions, the *why*. Leave out what it can discover by
  reading the code (stack, file tree, routes). Stale context is worse than none.

## What's in this lab
| File (in the sandbox) | Demonstrates |
|---|---|
| `CLAUDE.md` | Short project truths, an eager `@import`, a lazy pointer, a canary |
| `docs/architecture.md` | Imported eagerly with `@docs/architecture.md` |
| `docs/glossary.md` | Only referenced, never imported. It is **stale on purpose** (says `complete`, the code says `done`) |
| `taskboard/CLAUDE.md` | Nested file: loads when Claude reads anything in `taskboard/` |
| `.claude/rules/testing.md`, `cli.md` | Path-scoped rules (`paths:` frontmatter) |
| `AGENTS.md` | Ignored while `CLAUDE.md` exists (an exercise below proves it) |
| `CLAUDE.local.md.example` | Personal, gitignored instructions that load last |
| `.claude/hooks/log_instructions.py` | An `InstructionsLoaded` hook that logs each file as it enters the context |

## Try it
```bash
./lab new 01-claude-md
cd .sandbox/01-claude-md-*        # the path printed by ./lab new
tail -f .claude/logs/instructions.log &   # or run this in a second terminal
claude --setting-sources project,local
```
1. Type `/memory` to list the instruction files that are loaded. Type `/context` to see how many tokens they cost.
2. Ask: *"Read taskboard/cli.py and tests/test_cli.py. How does the CLI report errors?"* Then watch the log:
   ```
   12:53:35  session_start      CLAUDE.md
   12:53:35  include            docs/architecture.md      ← eager @import, loaded at launch
   12:53:38  nested_traversal   taskboard/CLAUDE.md        ← lazy: first read inside taskboard/
   12:53:38  path_glob_match    .claude/rules/cli.md       ← lazy: cli.py matched its paths:
   12:53:38  path_glob_match    .claude/rules/testing.md   ← lazy: a test file matched
   ```
3. Ask: *"Fix ticket tickets/T01-fix-done-counter.md."* Then watch whether Claude opens `docs/glossary.md`, and
   which source it trusts: the stale glossary (`complete`) or `STATUSES` in the code (`done`).

## What to observe
- **Eager vs lazy** in the log timestamps. Everything with `session_start` / `include` is paid for on every turn.
- **The contradiction** in step 3. The CLAUDE.md rule ("status names come only from `STATUSES`") should win. If
  Claude "fixes" `STATUSES` to `complete` instead, the stale doc beat the code. That is the course's "the rules lie
  about the repository" case. Only a human can decide which source is true.
- **The canary**: every final answer should end with `pygmalion`. If it stops appearing (try `/compact` a few times
  in a long session), instructions were lost.

## Exercises
1. **AGENTS.md precedence.** `mv CLAUDE.md CLAUDE.md.off`, start a new session, then run `/memory`: now AGENTS.md
   loads. Restore CLAUDE.md and add the line `@AGENTS.md` at the top so one shared file serves every tool.
2. **Eager vs lazy cost.** Change the glossary pointer to an import (`@docs/glossary.md`), restart and compare the
   memory line in `/context`. Then turn the architecture import into a backtick pointer.
3. **Fix the stale doc.** Update `docs/glossary.md` to `done`. Rerun step 3 in a fresh sandbox and compare.
   Measure it with `./lab run 01-claude-md --ticket T01` against `./lab run 01-single-agent --ticket T01`.
4. **Personal layer.** `cp CLAUDE.local.md.example CLAUDE.local.md` and see it appear last in `/memory`.
5. **Write a rule.** Add `.claude/rules/report.md` scoped to `taskboard/report.py` ("all user text must go through
   `html.escape`"). Ask Claude to work on the export and check the log for `path_glob_match`.

## Takeaways
- Small, true, specific context beats big context. Every always-loaded line is paid for in every session by everyone.
- Use imports to organize, nested files and path rules to save tokens, and plain pointers for rarely needed detail.
- An instruction is a suggestion. When something must *always* happen, use a hook (lab 04).
