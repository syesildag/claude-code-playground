# 10: Langfuse, trace, monitor, evaluate

> Lab 04's `events.log` shows *that* the agent did something. Langfuse shows *everything*: each turn, every model
> call with its tokens, every tool call, grouped by session and searchable by tag. And `./lab run --trace` puts the
> hidden-test verdict next to it as a score.
> Course: AI Fluent 2 M7 (LLMOps: trace, monitor, evaluate), AI Fluent 1 M3 (cost), M7 (scoring).

## The concept
- **Three pillars** (from the course): **trace** (what the agent did, step by step), **monitor** (cost, latency,
  model mix), **evaluate** (scores: deterministic like "hidden tests pass", or an LLM judge).
- **Observability ≠ gateway.** Langfuse *observes* and scores. A gateway (LiteLLM) *routes* and fails over.
  Installing one doesn't give you the other.
- **How sessions get there:** Langfuse's **official Claude Code plugin** (`langfuse-observability`) runs a hook on
  `Stop` and `SessionEnd`, reads the session transcript, and uploads it with the Langfuse SDK. One trace per
  conversational turn, grouped by Claude's session id.
- **Self-hosted on purpose:** traces contain your prompts and your code. Here everything stays on `localhost`.
- **Langfuse v4 note:** v4 runs in *events_only* mode. The older read APIs (`/api/public/traces`, `/sessions`, score
  listing) return 404, reads go through `/api/public/v2/observations`, and `POST /api/public/scores` still works.
  Older tutorials predate this.

## What's in this lab
| Piece | Role |
|---|---|
| `server/docker-compose.yml` | Pinned copy of Langfuse's official compose file (**v4.80.0**): web, worker, AI gateway, Postgres, ClickHouse, Redis, MinIO |
| `server/docker-compose.lab.yml` | Lab override: every port on **127.0.0.1** (upstream exposes 3000, 3031 and 9090 to the network), MinIO moved to **9190** (Ubuntu's Cockpit owns 9090) |
| `server/.env` (generated, gitignored) | Random secrets plus *headless init*: the org, project `claude-code-lab`, login and API keys exist at first boot, so there's no sign-up |
| `./lab langfuse up \| down [--wipe] \| status \| open` | Start, stop and inspect the stack (repo root) |
| `--trace` on `./lab new` and `./lab run` | Enables the plugin **for that sandbox only** (`claude plugin install … --scope local`) and points it at localhost with env vars |
| `lablib/langfuse.py` | The helpers behind it (stdlib). Tests in `tests/` run offline in `./lab check` |

This lab's own sandbox is always traced (`"trace": true` in `lab.json`).

## Setup (once)
1. **Docker Desktop running**, with *Settings → WSL integration → Ubuntu* enabled if you're on WSL. Check with
   `docker version`: it must show a **Server** section.
2. **uv** (the plugin's runtime): `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. **Start Langfuse:** `./lab langfuse up`. The first run pulls about 3–4 GB of images. It prints the URL and the
   generated login (`lab@example.com` / a random password from `server/.env`).

## Try it
```bash
./lab new 10-langfuse          # always traced: refuses to start if Langfuse is down
cd .sandbox/10-langfuse-*
claude --setting-sources project,local
```
1. Ask: *"Fix tickets/T01-fix-done-counter.md."* Wait for the answer (the hook uploads when the turn stops).
2. Open http://localhost:3000, log in, then **Tracing** → your turn. Expand the tree: the *Conversational Turn*,
   each *LLM Call* (model, input/output tokens, cache reads), each *Tool: Read / Edit / Bash*.
3. **Sessions** groups your turns. Ask a follow-up and watch a second trace join the same session.

## The testbed in Langfuse
```bash
./lab run 01-single-agent --ticket T01 --model haiku --trace
```
Verified output:
```
▶ [1/1] 01-single-agent × T01  (sandbox: 01-single-agent-…-run-T01)
  ✔ ACCEPTED  acceptance: OK
  cost $0.011 · turns 12 · 32.1s · 2 files changed · regressions 0 · fixed 1 · permission denials 2
  cost by model: claude-haiku-5-5 $0.011
  langfuse: 1 trace(s) → http://localhost:3000/project/claude-code-lab/sessions/7748ed99-…
```
What Langfuse held for that session:

| What | Value |
|---|---|
| Observations | 28: 1 turn span, **16 LLM calls** (`claude-haiku-5-5`, token usage), **11 tool calls** (Bash, Edit, Read, Write) |
| Trace tags | `claude-code`, `lab:01-single-agent`, `kind:architecture`, `ticket:T01`, `model:haiku`, `run:1` |
| Scores on the session | `accepted = 1` (BOOLEAN, comment `OK`) · `regressions = 0` (NUMERIC) |

A run **without** `--trace` sends nothing (verified: 0 observations for its session).

Now compare two architectures on the same ticket:
```bash
./lab run 01-single-agent --ticket T03 --trace --repeat 2
./lab run 02-planner-executor-verifier --ticket T03 --trace --repeat 2
```
In Langfuse, filter traces by tag `ticket:T03`, then by `lab:…`. Open one session of each and compare: how many
LLM calls, how many tool calls, which files were read more than once, where the subagents sit in the tree, and
whether `accepted` is 1.

## What to observe
- **Tokens vs cache:** most input tokens of a turn are *cache reads*. A sudden jump in uncached input points to
  a changed prompt prefix.
- **Tool loops:** the same `Tool: Read` on one file several times usually means the agent lacked context.
- **Counts in `results/*.json`:** `langfuse_observations` and `langfuse_traces` are read once two polls agree (ingestion is asynchronous). If Langfuse is still ingesting when the 60 s lookup ends, they're a lower bound.
- **Cost:** Langfuse shows a cost only for models it has a price for. A model as new as `claude-haiku-5-5` may show
  none. Claude Code's own figure is in `results/*.json` (`cost_usd`, `cost_by_model`).

## Exercises
1. **Diagnose waste** (the course demo): find a run with repeated reads, add a "where to look" hint to the lab's
   `CLAUDE.md`, rerun with `--trace`, and compare the two sessions.
2. **LLM-as-a-judge:** in Langfuse, add an LLM connection (needs a model API key), then an evaluator such as "did the
   agent stay within the ticket's scope?". Compare its scores with the deterministic `accepted` score.
3. **The OTel route:** start a sandbox session with `CLAUDE_CODE_ENABLE_TELEMETRY=1`,
   `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA=1`, `OTEL_TRACES_EXPORTER=otlp`,
   `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://localhost:3000/api/public/otel/v1/traces`,
   `OTEL_EXPORTER_OTLP_TRACES_PROTOCOL=http/protobuf` and a Basic auth header made from the keys. What arrives,
   compared with the plugin?
4. **Decide what you trace:** `CC_LANGFUSE_MAX_CHARS` truncates captured inputs and outputs. What would you cap
   before using this on real client code?
5. **Model prices:** add a custom model definition for `claude-haiku-5-5` in Langfuse's settings and check that
   costs appear on new traces.

## Troubleshooting
| Symptom | Cause and fix |
|---|---|
| `Docker isn't reachable` | Start Docker Desktop. On WSL, turn *WSL integration → Ubuntu* off and on again if `/var/run/docker.sock` is missing |
| `these ports are already in use: …` | Something else listens there: `ss -ltnp`, or on Windows `netstat -ano`. We already moved MinIO to 9190 because of Cockpit |
| `⚠ No Langfuse traces for session …` | The plugin hook didn't upload. Check `~/.claude/state/langfuse_hook.log`, set `CC_LANGFUSE_DEBUG=true`, and run `./lab langfuse status` (runtime, health) |
| `server/.env is missing but Langfuse's data volumes still exist` (from `up`) | `.env` was deleted (for example by `git clean -fdX`) while the database survived. A new `.env` can't open it: restore the old file, or `./lab langfuse down --wipe`, then `up` |
| `Langfuse rejected the lab's API keys` (from `--trace`) | Same cause, caught before a paid run starts: `./lab langfuse down --wipe`, then `up` |
| `couldn't install langfuse-observability for this sandbox` | The plugin install failed (often no network) and the plugin isn't downloaded yet. The message shows Claude Code's error. Retry, or run the printed command inside the sandbox |

## Teardown
`./lab langfuse down` stops everything and keeps the data. `./lab langfuse down --wipe` also deletes all traces and
users. The plugin stays installed only for the sandboxes you traced. Your other Claude Code sessions never load it.

## Takeaways
- You can't improve what you can't see: trace first, then optimize cost, tools and context.
- Put the deterministic verdict (`accepted`) next to the trace, so "it looked busy" and "it worked" don't get confused.
- Self-host anything that captures prompts and code.
