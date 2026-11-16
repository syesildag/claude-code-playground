# 03: Subagents

> A subagent is a specialist that Claude spawns with a **fresh context window**, its **own tools** and its **own
> model**. It does the noisy work (reading 20 files, running tests) and returns only a summary.
> Course: AI Fluent 1 M3–M4, AI Fluent 2 M1–M2.

## The concept
- File: `.claude/agents/<name>.md`, YAML frontmatter plus a system prompt. Only `name` and `description` are
  required. Claude decides when to delegate from the `description`, so phrases like "use proactively" help.
- **`tools`** is an allowlist (least privilege). An agent without Edit doesn't even *try* to edit, which also
  sharpens its focus. Accepting someone else's agent means accepting every tool it declares.
- **`model`** (`haiku` / `sonnet` / `opus` / `inherit`): routing by the *nature* of the task. Mechanical work goes
  to small models, judgment to big ones.
- **Isolation cuts both ways.** It keeps your main context clean, but each subagent re-reads the files it needs,
  so a trivial task costs *more* with delegation.
- Extras shown here: `hooks:` scoped to one agent, `skills:` to preload, `memory:` to persist across sessions,
  `maxTurns:` as a safety stop.

## What's in this lab
| Agent | Tools | Model | Demonstrates |
|---|---|---|---|
| `code-explorer` | Read, Grep, Glob | haiku | Read-only exploration; strict return format; "use proactively" |
| `test-runner` | Bash, Read | haiku | A `PreToolUse` hook **in its frontmatter** that only allows `python3 -m unittest`; `maxTurns` |
| `security-reviewer` | Read, Grep, Glob | sonnet | `skills: [security-checklist]` preloaded at start; PASS/FAIL contract |
| `doc-keeper` | Read, Grep, Glob, Edit, Write | haiku | `memory: project` → `.claude/agent-memory/doc-keeper/MEMORY.md` |

## Try it
```bash
./lab new 03-subagents    # then: cd into the sandbox && claude --setting-sources project,local
```
1. `/agents` lists every agent, built-in and project. Open one to see its tools and model.
2. *"How does persistence work in this project?"* Claude should delegate to `code-explorer` on its own (description
   match). Then run `/context` and see how little the exploration cost your main session.
3. *"Use the test-runner agent to check the tests."* You get one failure (T01), reported in three lines.
4. *"Ask test-runner to delete board.json."* Its own hook denies anything that isn't `python3 -m unittest`.
5. `@"security-reviewer (agent)" review taskboard/report.py`: expect `VERDICT: FAIL` and the XSS in `export_html`.
6. *"Have doc-keeper check the README."* Then look at `.claude/agent-memory/doc-keeper/MEMORY.md`, start a new
   session and ask again. Does it remember?

## What to observe
- **Ctrl+O** shows each subagent's own transcript. The main thread only receives the final message.
- **Background agents:** subagents can run while you keep working.
- `claude --setting-sources project,local --agent code-explorer` runs the *whole session* as that agent, with its
  tools and prompt.

## Exercises
1. **Same question, two ways.** Ask "where is the status validated?" once with no agents (the
   `--disallowed-tools Agent` flag) and once via `code-explorer`. Compare `/context` and `/cost`.
2. **Parallel fan-out.** *"Run security-reviewer on report.py and store.py in parallel."* Two agents, one message.
   That's the seed of `architectures/04-fan-out-fan-in`.
3. **Swap the model.** Set `security-reviewer` to `model: haiku`. Does it still find the XSS? The non-atomic save?
4. **Least privilege.** Remove `tools:` from `code-explorer`. It now inherits everything, including Edit and Bash.
   Why is that worse even if it never edits?
5. **Write one.** Run `/agents` → "Create new agent" and let Claude draft a `perf-reviewer`. Then compare it with
   `architectures/04-fan-out-fan-in/overlay/.claude/agents/performance-reviewer.md`.

## Takeaways
- Delegate to *isolate context*, *parallelize*, *specialize* or *get an independent review*. Otherwise stay single-agent.
- Every agent: precise description, minimal tools, a deliberate model, a strict return format.
- Hooks in frontmatter apply only while that agent runs, which makes them good for per-role guardrails.
