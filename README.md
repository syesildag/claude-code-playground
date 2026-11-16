# Claude Code Playground

Hands-on labs for learning **Claude Code's building blocks** (CLAUDE.md, skills, subagents, hooks, permissions,
output styles, MCP, plugins, headless mode), plus a **testbed for comparing agent architectures** (single agent,
planner/executor/verifier, pipelines, fan-out, orchestrators, gated TDD) on the same tickets with hidden,
deterministic acceptance tests.

Every lab runs against one small practice app, a Python "taskboard" with **deliberately planted problems**: a
counting bug, an HTML-injection hole, a save that can corrupt data, and a slow lookup. Agents have something real to
find, fix and review.

Everything here was checked against a real Claude Code (v2.1.318) while it was built: hooks firing, rules denying,
MCP handshakes, plugin loading. The READMEs show the observed output, not guesses.

## Quick start

Requirements: [Claude Code](https://code.claude.com), Python 3.10+, git. No other dependencies (stdlib only).

```bash
git clone https://github.com/syesildag/claude-code-playground.git
cd claude-code-playground
./lab check                 # offline validation of every lab and ticket (no model calls)
./lab list                  # all labs
./lab new 04-hooks          # build a sandbox for a lab and print how to start Claude in it
```

Then follow the lab's `README.md` (for example [concepts/04-hooks](concepts/04-hooks/README.md)).

## How labs run: sandboxes

```
app/  +  tickets/  +  <lab>/overlay/   ──./lab new──►   .sandbox/<lab>-<timestamp>/   (its own git repo, baseline commit)
```

- Each sandbox is a **fresh copy**, so you can break things, `git diff` what the agent did, and throw it away.
- Start Claude with `claude --setting-sources project,local`. This **clean room** skips your personal
  `~/.claude/settings.json`, so your own plugins, skills and hooks don't leak into the lab. (In our tests it took a
  session from 25 loaded plugins down to only the built-ins.)
- The repo's own `CLAUDE.md` (an authoring guide) is kept out of sandboxes with `claudeMdExcludes`, because
  CLAUDE.md files load from every parent directory.
- The first interactive launch in a sandbox asks you to **trust the folder**. Until you do, allow rules in
  `.claude/settings.json` are ignored (deny rules and hooks still apply).

## Concept labs

| Lab | You learn |
|---|---|
| [01 CLAUDE.md & context](concepts/01-claude-md/README.md) | Eager `@imports` vs lazy nested files and path-scoped rules (an `InstructionsLoaded` hook logs each load), AGENTS.md precedence, stale-doc contradictions, a canary word |
| [02 Skills](concepts/02-skills/README.md) | Descriptions as activation conditions, manual-only vs model-only skills, `$ARGUMENTS`, supporting files, `` !`command` `` live data, `context: fork` |
| [03 Subagents](concepts/03-subagents/README.md) | Tool allowlists, a model per agent, hooks scoped to one agent, preloaded skills, persistent `memory` |
| [04 Hooks](concepts/04-hooks/README.md) | Eight hooks across the lifecycle: context injection, prompt guard, dangerous-command denial, protected tests, secret scanning, a Stop gate on red tests, an event logger |
| [05 Permissions & injection](concepts/05-permissions/README.md) | allow/ask/deny, modes, precedence. A ticket with a hidden prompt injection tries to leak fake secrets |
| [06 Output styles & status line](concepts/06-output-styles-statusline/README.md) | A Socratic-tutor style, a findings-only style, a status line showing context and cost |
| [07 MCP](concepts/07-mcp/README.md) | A hand-written stdio MCP server (~150 lines, no SDK), approval, tool naming, protocol logging |
| [08 Plugins & marketplaces](concepts/08-plugins/README.md) | Package a skill, an agent and a policy hook as a versioned plugin in a local marketplace |
| [09 Headless & CI](concepts/09-headless/README.md) | `claude -p` with JSON Schema output as a CI gate, and a live trace of tool calls, cost and cache use |

## Architecture labs (the testbed)

| Lab | Pattern | Run it on a ticket |
|---|---|---|
| [A1 Single agent](architectures/01-single-agent/README.md) | The control group: one agent, no extras | `./lab run 01-single-agent --ticket T01` |
| [A2 Planner / Executor / Verifier](architectures/02-planner-executor-verifier/README.md) | Opus plans, Sonnet executes, gates run, a fresh-context verifier judges only the diff | `./lab run 02-planner-executor-verifier --ticket T03` |
| [A3 Sequential pipeline](architectures/03-sequential-pipeline/README.md) | Spec → code → tests, each role fenced to its own directory | `./lab run 03-sequential-pipeline --ticket T02` |
| [A4 Fan-out / fan-in](architectures/04-fan-out-fan-in/README.md) | Four parallel reviewers and a consolidator, scored for recall of the planted issues | `bash scripts/compare-reviews.sh` (in the sandbox) |
| [A5 Orchestrator](architectures/05-orchestrator/README.md) | The session *is* an orchestrator that routes tickets, verifies with tools and escalates | `./lab run 05-orchestrator --ticket T02` |
| [A6 Gated TDD](architectures/06-gated-tdd/README.md) | RED → GREEN → cold review → proof page, with scripted stop gates and a Stop hook | `./lab run 06-gated-tdd --ticket T02` |

### Running experiments

```bash
./lab run 01-single-agent --ticket T03 --model sonnet --repeat 3
./lab run 02-planner-executor-verifier --ticket T03 --repeat 3
./lab compare --ticket T03
```

`./lab run` builds a fresh sandbox, runs the lab headlessly (`claude -p`, budget-capped, clean room), then scores it:

| Metric | Meaning |
|---|---|
| **accepted** | The ticket's **hidden acceptance tests** pass. They're copied in only after the agent finishes, so it can't read or game them |
| regressions / fixed | Tests that newly fail or newly pass, compared with the sandbox's own baseline |
| cost, cost by model | From Claude Code's own accounting (`modelUsage`): shows where model routing spends money |
| turns, wall time, files changed, permission denials | How the agent worked. Headless runs may only run the tests, the CLI and read-only git. Ad-hoc `python3 -c` scripts are denied on purpose (that would be arbitrary code), and the denials are recorded |

A real run, for scale: `./lab run 01-single-agent --ticket T01 --model haiku` was accepted with 0 regressions, in
10 turns, 23 s, for $0.009.

Results are saved as JSON in `results/` (gitignored). Agents are non-deterministic, so compare with `--repeat 3`
or more, and keep `--model` the same across labs. Subagents use the model in their own frontmatter, because
routing is part of the architecture. Labs with Opus subagents cost more. `--budget` caps each run (default $2).

### Tickets

[tickets/](tickets/README.md) holds four AI-ready work items (goal, context to read, constraints, testable
acceptance criteria, out of scope): **T01** a bug with a failing test, **T02** a multi-file feature with backward
compatibility, **T03** a reliability fix that no existing test catches, and **T04** a security fix where every test
is already green. `./lab check` proves each hidden test **fails on the baseline** and **passes with a reference
solution**.

## What surprised us (checked on Claude Code v2.1.318)

Things that differ from older notes and course material, all observed while building this repo:

- **AGENTS.md is read natively** when no CLAUDE.md exists (v2.1.277+). With a CLAUDE.md present it's ignored,
  unless you import it with `@AGENTS.md`.
- **Untrusted folders ignore project allow rules**, even in headless `-p` runs. Rules passed with `--settings` still
  apply. `./lab run` relies on that.
- **Unknown frontmatter fields are silently ignored**, and `claude plugin validate` accepts bad values (`context:
  forked`, `model: gpt-4`). A typo like `tool:` instead of `tools:` gives an agent *every* tool. `./lab check`
  includes a linter for this.
- **MCP handshake:** Claude Code first probes `server/discover` (a 2026 protocol), then falls back to `initialize`.
  You can watch it in lab 07's protocol log.
- **`claude -p` waits 3 seconds for stdin** in scripts. Add `< /dev/null`.
- The subagent tool is called `Agent` (formerly `Task`). `tools: Agent(a, b)` limits which subagents a main-session
  agent may spawn.
- Hooks have over 30 events, an `if` filter (`"if": "Bash(git commit*)"`), and `prompt`, `agent`, `http` and
  `mcp_tool` types next to `command`.

## Add your own lab

```bash
./lab scaffold concepts 10-my-topic     # or: architectures 07-my-pattern
```
Or open Claude Code at the repo root and say *"create a new lab about X"*. The repo's own `new-lab` skill walks
through it. Conventions live in [CLAUDE.md](CLAUDE.md): stdlib Python, hooks tested offline, least-privilege agents
with an explicit model. Finish with `./lab check`.

## Repository layout

```
app/                 practice app (taskboard) copied into every sandbox; its bugs are intentional
tickets/             work items, hidden acceptance tests, reference patches
concepts/NN-*/       concept labs: lab.json, README.md, overlay/, tests/
architectures/NN-*/  architecture labs, same structure, runnable with ./lab run
templates/lab/       skeleton for ./lab scaffold
lab                  the CLI: list, new, run, compare, inspect, check, scaffold, clean
.claude/             Claude Code config for authoring this repo (the new-lab skill)
```

The lab content is based on an internal AI-assisted development training track (AI Foundation and AI Fluent, Core
AI SDLC). Each lab README names the module it relates to.
