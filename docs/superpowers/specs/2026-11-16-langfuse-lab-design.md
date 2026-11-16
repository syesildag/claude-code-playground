# Design: Langfuse observability lab and `--trace` switch

Date: 2026-11-16 · Status: draft for approval

## Intent

The user asked how to debug agents and AI flows, then asked for a self-hosted **Langfuse** showcase in this repo.
Langfuse is the LLMOps tool the course uses (AI Fluent 2 M7: trace, monitor, evaluate). The showcase should let a
learner see every turn, model call, tool call, token count and cost of a Claude Code session in a real observability
UI, and use that UI to compare the repo's agent architectures.

## Goals

1. **One command starts a local Langfuse** with no manual setup: org, project, login and API keys pre-created.
2. **Langfuse's official Claude Code plugin** (`langfuse-observability`) sends the sessions, configured per sandbox,
   never globally.
3. **A new concept lab `concepts/10-langfuse`** with a README in the repo's lab format (concept, try it, observe,
   exercises).
4. **A `--trace` switch for every lab**: `./lab new <lab> --trace` and `./lab run <lab> --ticket T0x --trace` send
   sessions to Langfuse, tagged by lab, ticket and model. `lab run` also posts the hidden-test verdict as a Langfuse
   score, so Langfuse becomes the testbed's dashboard.
5. **Verified end to end** on this machine before it's called done.

## Non-goals

- A production Langfuse deployment (TLS, SSO, backups, scaling).
- Langfuse Cloud. Everything stays on localhost.
- Writing our own exporter (option 1 below, not chosen) or modifying the plugin.
- Automated LLM-as-a-judge. It's an exercise only, since it needs a model API key in Langfuse.

## Anti-goals (failure even if it works)

- Langfuse reachable from the network (upstream binds ports 3000 and 9090 to all interfaces).
- Any real or generated key committed to this **public** repo.
- The plugin enabled at user scope, so the user's other Claude Code sessions run its hook or send data.
- Labs without `--trace` behaving differently, or `./lab check` needing Docker or network.
- Silently installing software (uv, the plugin, Docker images) without the user knowing.

## Constraints (verified on this machine, 2026-11-16)

- Claude Code 2.1.318 on WSL2. Docker CLI 29.9 and Compose v5.7 are installed, but **Docker Desktop is not running**.
  19 GiB RAM, 16 cores, about 900 GB free.
- Langfuse latest release **v4.80.0** (2026-11-13). The upstream `docker-compose.yml` runs `langfuse-web` (3000),
  `langfuse-worker` (3030), `langfuse-ai-gateway`, `clickhouse` (8123, 9000), `minio` (9090, 9091), `redis` (6379)
  and `postgres` (5432). It supports headless init via `LANGFUSE_INIT_*` variables (org, project, public and secret
  key, user email and password).
- Plugin `langfuse-observability` v1.2.0 is listed in the installed `claude-plugins-official` marketplace, pinned to
  commit `b5211009698fdfe79c6bbe90d6901ad255ea65d3` (MIT). Reviewed:
  - Hooks on `Stop` and `SessionEnd`. Runs `uv run --script` if `uv` is on PATH, otherwise `python3` (which then
    needs `langfuse>=4.7,<5` installed). **Neither `uv` nor the SDK is installed.**
  - Config: plain env vars **win over** the plugin's stored userConfig (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`,
    `LANGFUSE_BASE_URL`, `LANGFUSE_USER_ID`). Extra tags via `CC_LANGFUSE_TRACE_TAGS` (comma list or JSON array, max
    20). One trace per turn ("Conversational Turn"), grouped by Claude `session_id`. Default tag `claude-code`, plus
    `skill:<name>` tags.
  - Fails open: if keys or runtime are missing it logs to `~/.claude/state/langfuse_hook.log` and exits.
- `claude plugin install <p> --scope local` exists, so the plugin can be enabled for one project directory only.
- Repo conventions (root `CLAUDE.md`): the repo's own tooling is stdlib Python. Hook and lab scripts are tested
  offline. `./lab check` stays offline.
- Earlier verified behaviour to respect: untrusted folders ignore **allow rules** from `.claude/settings.json`, while
  `--settings` and hooks still apply. Headless `-p` runs need `< /dev/null`.

## Approaches considered

| | Approach | Trade-off | Decision |
|---|---|---|---|
| 1 | Hand-written stdlib Stop hook sending OTLP to Langfuse | Fully transparent and project-scoped, but ours to maintain and not the official route | Not chosen |
| 2 | **Langfuse's official plugin** | The real product path, maintained by Langfuse, rich traces (subagents, skills, images). Needs `uv` and must be enabled per sandbox | **Chosen by the user** |
| 3 | Claude Code's built-in OTel export to Langfuse's OTLP endpoint | Zero code, but traces are beta, Langfuse's endpoint is HTTP-only, and there are reports of nothing showing up | An exercise in the lab |

| | Scope | Trade-off | Decision |
|---|---|---|---|
| A | Tracing only inside lab 10 | Smaller | Not chosen |
| B | **Lab 10 plus a `--trace` switch for all labs, with acceptance scores** | About twice the work, but Langfuse becomes the testbed's dashboard | **Chosen** (user: "you decide") |

## Design

### Files

```
concepts/10-langfuse/
  lab.json            kind concept, "trace": true (./lab new always traces this lab)
  README.md
  server/
    docker-compose.yml        pinned copy of upstream v4.80.0, with a header naming source URL, tag and date
    docker-compose.lab.yml    override: web and minio bound to 127.0.0.1, LANGFUSE_IMAGE_TAG pinned to 4.80.0
    .env.example              every variable the lab sets, with placeholder values
    .env                      GENERATED by ./lab langfuse up, gitignored, chmod 600
  overlay/
    .claude/settings.json     allow rules for the test command (same as other labs)
  tests/
    test_langfuse_helpers.py  offline: env generation, tag building, score payload, settings merge
```
Root `.gitignore` gains `concepts/10-langfuse/server/.env`.

### `./lab langfuse up | down [--wipe] | status | open`

- `up`: if `server/.env` is missing, generate it. That means random secrets for NEXTAUTH_SECRET, SALT,
  ENCRYPTION_KEY (64 hex), the DB, ClickHouse, Redis and MinIO passwords, and the init values: org `lab`, project
  `claude-code-lab`, user `lab@localhost` with a random password, public key `pk-lf-<hex>`, secret key `sk-lf-<hex>`.
  Then run `docker compose -f docker-compose.yml -f docker-compose.lab.yml up -d`, poll
  `http://localhost:3000/api/public/health` (timeout about 3 minutes, first image pull excepted), and print the URL
  and login. Fail with a clear message if Docker isn't reachable ("start Docker Desktop") or a port is taken.
- `down` stops the containers. `--wipe` also removes the volumes (and asks for confirmation).
- `status` shows container health plus whether the plugin is installed and `uv` is on PATH.
- `open` prints the UI URL and login.

### `--trace` on `./lab new` and `./lab run`

Before building the sandbox, preflight checks. Each failure stops with the exact command to fix it, and never
auto-installs:
1. Langfuse is healthy and `server/.env` exists. Otherwise: `./lab langfuse up`.
2. A runtime exists: `uv` on PATH, or `python3 -c "import langfuse"`. Otherwise, print how to install uv.

Then, in the sandbox:
3. Enable the plugin for that directory only: run `claude plugin install langfuse-observability@claude-plugins-official --scope local`
   inside the sandbox (non-interactive). If a local-scope install turns out not to work as expected, fall back to
   writing `enabledPlugins` into the sandbox's `.claude/settings.local.json`. Decide during implementation by
   testing.
4. Point the plugin at the local server through env vars, from `server/.env`: `LANGFUSE_PUBLIC_KEY`,
   `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL=http://localhost:3000`, `LANGFUSE_USER_ID=lab`, and
   `CC_LANGFUSE_TRACE_TAGS=lab:<name>,kind:<concept|architecture>` (plus `ticket:<id>,model:<m>,run:<n>` in
   `lab run`). They go in the sandbox's `settings.local.json` `env` block for interactive use. `lab run` also passes
   them in the `claude` subprocess environment, which hooks inherit, so it doesn't depend on folder trust.

`./lab run --trace`, after the run:
5. Post scores on the session through Langfuse's public API (stdlib `urllib`, basic auth with the lab keys):
   `accepted` (boolean or 0/1) with the acceptance summary as comment, and `regressions` (number).
6. Save `langfuse_session_url` in the result JSON and print it.

Without `--trace`, nothing changes.

### Lab 10 README (outline)

1. Concept: the three LLMOps pillars (trace, monitor, evaluate), gateway vs observability (from the course), and
   what the plugin captures. Privacy: prompts and code go to the trace store, which is why it's self-hosted.
2. Setup: start Docker Desktop, install uv, `./lab langfuse up`, `./lab new 10-langfuse`, log in.
3. Try it: a session on T01, then the trace tree (turn → LLM calls → tools), the session view, filtering by tags.
4. Testbed: `./lab run 01-single-agent --ticket T03 --trace` and `./lab run 02-planner-executor-verifier --ticket T03 --trace`,
   then compare in Langfuse (latency, tokens, cost per model, the `accepted` score).
5. Exercises: diagnose waste (re-read files, then add a CLAUDE.md hint, then rerun and compare; the course M7
   demo); an LLM-as-a-judge evaluator (optional, needs an API key); the OTel route (approach 3) and what shows up;
   `CC_LANGFUSE_MAX_CHARS` and what data you're willing to trace; compare with lab 04's `events.log`.
6. Teardown: `./lab langfuse down [--wipe]`.

### Verification ("done" means all of these were observed)

1. `./lab check` passes offline, including the new helper tests.
2. `./lab langfuse up` → health OK, and the UI login works with the generated credentials.
3. `./lab run 01-single-agent --ticket T01 --model haiku --trace` → Langfuse's API returns traces tagged
   `lab:01-single-agent` with generations carrying token usage. An `accepted` score exists on the session, and the
   printed session URL opens.
4. The plugin is **not** enabled at user scope afterwards (`claude plugin list` outside a sandbox).
5. A run **without** `--trace` still works and sends nothing.
6. `./lab langfuse down` stops everything.

## What needs the user at build time

Starting Docker Desktop. Consent to install `uv` and to pull about 3–4 GB of images. The first plugin install
(it fetches the plugin's git source at the pinned commit).

## Calls made during the builder check (the designer's, not the user's)

- **Lab 10 always traces.** If Langfuse isn't up, `./lab new 10-langfuse` stops and prints `./lab langfuse up`
  rather than building an untraced sandbox.
- **Scores attach to the session** (`sessionId`). If the API rejects session scores, attach them to the session's
  last trace, found with a traces query by `sessionId`.
- **Upstream services stay as shipped**, including `langfuse-ai-gateway`. Only if one fails to start without
  extra config does the override file disable it, and the README says so.

## Left to the builder

The exact score data type (BOOLEAN vs NUMERIC) as the API accepts it, health-poll timing, how to detect "plugin
installed" (`claude plugin list --json`), whether `env` in `settings.local.json` applies before trust (document
whichever is observed), port-conflict messages, and README wording.
