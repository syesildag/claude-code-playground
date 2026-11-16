# Langfuse Lab and `--trace` Switch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Self-hosted Langfuse in one command, Langfuse's official Claude Code plugin wired per sandbox, a
`--trace` switch on `./lab new` and `./lab run` (tags plus acceptance scores), and a `concepts/10-langfuse` lab.

**Architecture:** Langfuse runs from a pinned copy of the upstream Docker Compose file plus a localhost-only override,
configured by a generated, gitignored `.env`. A new stdlib module `lablib/langfuse.py` holds the env generation,
tags, Langfuse API calls and Docker helpers. `./lab` gains a `langfuse` sub-command and a `--trace` flag that enables
the plugin with `--scope local` inside the sandbox and passes env vars to it.

**Tech Stack:** Python 3.10+ stdlib (`urllib`, `secrets`, `subprocess`, `socket`), Docker Compose v2.24+ (for
`!override`), Langfuse v4.80.0, plugin `langfuse-observability` v1.2.0, Claude Code 2.1.318.

**Spec:** `docs/superpowers/specs/2026-11-16-langfuse-lab-design.md`

## Global Constraints

- Langfuse server version **4.80.0**: `LANGFUSE_IMAGE_TAG=4.80.0` (if that tag doesn't pull, use `4` and note it in the README).
- Plugin id **`langfuse-observability@claude-plugins-official`** (pinned in that marketplace at commit `b5211009698fdfe79c6bbe90d6901ad255ea65d3`).
- Base URL the plugin is pointed at: **`http://localhost:3000`**.
- Plugin env vars, exactly: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`, `LANGFUSE_USER_ID=lab`, `CC_LANGFUSE_TRACE_TAGS`.
- Tag format: comma list `lab:<name>,kind:<concept|architecture>` plus, in `lab run`, `ticket:<T0x>,model:<model|default>,run:<n>`.
- Every published host port binds to **127.0.0.1** (upstream exposes 3000, 3031 and 9090 on all interfaces).
- No generated value is committed. `concepts/10-langfuse/server/.env` is gitignored and written with mode `0600`.
- The plugin is **never** enabled at user scope. `./lab` never installs software. It stops and prints the command instead.
- Without `--trace`, `./lab new` and `./lab run` behave exactly as before. `./lab check` needs no Docker and no network.
- Repo tooling is stdlib Python. Headless `claude -p` calls use `stdin=DEVNULL`.

## Review Focus

1. **A port is already taken** (3000, 3030, 3031, 5432, 6379, 8123, 9000, 9090, 9091): `langfuse up` names the port and stops, with no raw Docker error. → Task 3 `test_port_conflicts_detects_bound_port`.
2. **Docker Desktop isn't running:** `langfuse up` and `--trace` say "start Docker Desktop" and exit 1. → Task 3 `test_docker_ok_false_for_missing_binary`.
3. **`.env` regenerated after first boot:** headless init only runs on an empty database, so new keys would get 401 forever. `ensure_env` must never overwrite an existing file. → Task 2 `test_ensure_env_is_idempotent`.
4. **Traces never arrive** (no runtime, the hook crashed, or the flush was lost at exit): `lab run --trace` must say so and point to `~/.claude/state/langfuse_hook.log` instead of printing a dead link. → Task 5 `test_trace_warning_mentions_hook_log`.
5. **Langfuse unreachable while scoring:** the run's result JSON is still written, and scoring problems become warnings, not crashes. → Task 3 `test_post_scores_returns_errors_instead_of_raising`.

---

### Task 1: Langfuse server files

**Files:**
- Create: `concepts/10-langfuse/server/docker-compose.yml` (upstream copy)
- Create: `concepts/10-langfuse/server/docker-compose.lab.yml`
- Create: `concepts/10-langfuse/server/.env.example`
- Modify: `.gitignore` (add `/concepts/10-langfuse/server/.env`)
- Test: `concepts/10-langfuse/tests/test_server_files.py`

**Interfaces:**
- Produces: `SERVER_DIR = REPO / "concepts/10-langfuse/server"`, holding the two compose files (base first, override second).

- [ ] **Step 0: Branch and include the spec.** `git switch -c feat/langfuse-lab`, then `git add docs/superpowers/`.
- [ ] **Step 1: Write the failing tests** in `test_server_files.py`:
  - `test_upstream_copy_is_pinned`: the first lines of `docker-compose.yml` contain `https://github.com/langfuse/langfuse` and `v4.80.0`.
  - `test_override_binds_public_ports_to_localhost`: `docker-compose.lab.yml` contains `!override` and each of `127.0.0.1:3000:3000`, `127.0.0.1:3031:3031`, `127.0.0.1:9090:9000`.
  - `test_env_file_is_gitignored`: `git check-ignore -q concepts/10-langfuse/server/.env` exits 0 (run from REPO).
  - `test_merged_config_has_no_public_bindings` (skip if `shutil.which("docker")` is None): `docker compose -f docker-compose.yml -f docker-compose.lab.yml --env-file .env.example config --format json`, cwd `SERVER_DIR`. Every `services.*.ports[*].host_ip` equals `"127.0.0.1"`. This needs no Docker daemon.
- [ ] **Step 2: Run** `cd concepts/10-langfuse && python3 -m unittest discover -s tests -t tests`. Expected: FAIL (the files don't exist).
- [ ] **Step 3: Vendor upstream.** `gh api "repos/langfuse/langfuse/contents/docker-compose.yml?ref=v4.80.0" -q .content | base64 -d`, prefixed with a 3-line header comment: source URL, tag `v4.80.0`, date fetched, "do not edit, override in docker-compose.lab.yml".
- [ ] **Step 4: Write the override.** For `langfuse-web`, `langfuse-ai-gateway` and `minio`, use `ports: !override` with the localhost bindings above (minio console stays `127.0.0.1:9091:9001`). Change nothing else.
- [ ] **Step 5: Write `.env.example`** listing every key `generate_env` (Task 2) produces, with placeholder values like `change-me`, and comments saying `./lab langfuse up` generates the real file.
- [ ] **Step 6: Run the tests.** Expected: PASS (the docker test passes, or is skipped when there's no CLI).
- [ ] **Step 7: Commit** with `feat(langfuse): pinned self-hosting files bound to localhost`.

### Task 2: `lablib/langfuse.py` pure helpers

**Files:**
- Create: `lablib/__init__.py` (empty), `lablib/langfuse.py`
- Test: `concepts/10-langfuse/tests/test_langfuse_helpers.py` (puts the repo root on `sys.path` via `Path(__file__).resolve().parents[3]`)

**Interfaces:**
- Produces, in `lablib/langfuse.py`:
  - constants `REPO`, `SERVER_DIR`, `ENV_FILE = SERVER_DIR / ".env"`, `BASE_URL = "http://localhost:3000"`, `PLUGIN_ID = "langfuse-observability@claude-plugins-official"`, `IMAGE_TAG = "4.80.0"`, `HOOK_LOG = "~/.claude/state/langfuse_hook.log"`
  - `generate_env(token=secrets.token_hex) -> dict[str, str]`
  - `write_env(path: Path, values: dict[str, str]) -> None` (mode 0600) · `read_env(path: Path) -> dict[str, str]`
  - `ensure_env(path: Path = ENV_FILE) -> tuple[dict[str, str], bool]`: returns `(values, created)`
  - `trace_tags(lab: str, kind: str, **extra: object) -> str`: `extra` keys appended in call order, `None` values skipped
  - `plugin_env(env: dict[str, str], tags: str) -> dict[str, str]`
  - `score_payloads(session_id: str, accepted: bool, regressions: int, summary: str) -> list[dict]`
  - `session_url(env: dict[str, str], session_id: str) -> str`

`generate_env` keys and values (`t(n)` = `token(n)`):
`LANGFUSE_IMAGE_TAG=4.80.0`, `TELEMETRY_ENABLED=false`, `NEXTAUTH_URL=http://localhost:3000`,
`NEXTAUTH_SECRET=t(32)`, `SALT=t(32)`, `ENCRYPTION_KEY=t(32)` (64 hex), `POSTGRES_PASSWORD=p=t(16)`,
`DATABASE_URL=postgresql://postgres:{p}@postgres:5432/postgres`, `CLICKHOUSE_PASSWORD=t(16)`, `REDIS_AUTH=t(16)`,
`MINIO_ROOT_PASSWORD=m=t(16)` and the same `m` for `LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY`,
`LANGFUSE_S3_MEDIA_UPLOAD_SECRET_ACCESS_KEY` and `LANGFUSE_S3_BATCH_EXPORT_SECRET_ACCESS_KEY`,
`LANGFUSE_INIT_ORG_ID=lab-org`, `LANGFUSE_INIT_ORG_NAME=Claude Code Lab`, `LANGFUSE_INIT_PROJECT_ID=claude-code-lab`,
`LANGFUSE_INIT_PROJECT_NAME=claude-code-lab`, `LANGFUSE_INIT_PROJECT_PUBLIC_KEY=pk-lf-{t(16)}`,
`LANGFUSE_INIT_PROJECT_SECRET_KEY=sk-lf-{t(24)}`, `LANGFUSE_INIT_USER_EMAIL=lab@example.com`,
`LANGFUSE_INIT_USER_NAME=Lab`, `LANGFUSE_INIT_USER_PASSWORD=t(12)`.

- [ ] **Step 1: Write the failing tests:**
```python
def test_generate_env_keeps_shared_secrets_consistent(self):
    env = lf.generate_env()
    self.assertIn(f":{env['POSTGRES_PASSWORD']}@postgres:5432/", env["DATABASE_URL"])
    for k in ("LANGFUSE_S3_EVENT_UPLOAD_SECRET_ACCESS_KEY", "LANGFUSE_S3_MEDIA_UPLOAD_SECRET_ACCESS_KEY",
              "LANGFUSE_S3_BATCH_EXPORT_SECRET_ACCESS_KEY"):
        self.assertEqual(env[k], env["MINIO_ROOT_PASSWORD"])
    self.assertEqual(len(env["ENCRYPTION_KEY"]), 64)
    self.assertTrue(env["LANGFUSE_INIT_PROJECT_PUBLIC_KEY"].startswith("pk-lf-"))
    self.assertEqual(env["LANGFUSE_IMAGE_TAG"], "4.80.0")
    self.assertEqual(env["TELEMETRY_ENABLED"], "false")

def test_generate_env_covers_env_example(self):   # .env.example keys == generate_env keys
def test_write_env_is_private_and_round_trips(self):   # stat mode & 0o777 == 0o600; read_env(write_env(x)) == x
def test_ensure_env_is_idempotent(self):   # 2nd call returns created=False and identical values
def test_trace_tags(self):
    self.assertEqual(lf.trace_tags("01-single-agent", "architecture", ticket="T01", model="haiku", run=2),
                     "lab:01-single-agent,kind:architecture,ticket:T01,model:haiku,run:2")
    self.assertEqual(lf.trace_tags("10-langfuse", "concept", ticket=None), "lab:10-langfuse,kind:concept")
def test_plugin_env(self):   # exactly the 5 constraint keys; BASE_URL; keys copied from LANGFUSE_INIT_PROJECT_*
def test_score_payloads(self):
    p = lf.score_payloads("sess-1", True, 0, "OK")
    self.assertEqual([s["name"] for s in p], ["accepted", "regressions"])
    self.assertEqual((p[0]["value"], p[0]["dataType"], p[0]["sessionId"]), (1, "BOOLEAN", "sess-1"))
    self.assertEqual((p[1]["value"], p[1]["dataType"]), (0, "NUMERIC"))
def test_session_url(self):   # f"{BASE_URL}/project/claude-code-lab/sessions/sess-1"
```
- [ ] **Step 2: Run** them. Expected: FAIL (`ModuleNotFoundError: lablib`).
- [ ] **Step 3: Implement** the signatures above. `read_env` parses `KEY=VALUE` lines and skips blanks and `#` comments. Values contain no newlines and are written unquoted.
- [ ] **Step 4: Run.** Expected: PASS.
- [ ] **Step 5: Commit** with `feat(langfuse): env generation, tags and score payload helpers`.

### Task 3: Server control (`./lab langfuse`) and service helpers

**Files:**
- Modify: `lablib/langfuse.py` (add the service helpers)
- Modify: `lab` (add `sys.path.insert(0, str(REPO))`, `from lablib import langfuse as lf`, `cmd_langfuse`, and the sub-parser)
- Test: `concepts/10-langfuse/tests/test_langfuse_helpers.py`

**Interfaces:**
- Consumes: Task 2 helpers, and `SERVER_DIR` from Task 1.
- Produces:
  - `PORTS = (3000, 3030, 3031, 5432, 6379, 8123, 9000, 9090, 9091)`
  - `docker_ok(docker: str = "docker") -> bool`: `docker info` exits 0 within 15 s, and False on `FileNotFoundError`
  - `port_conflicts(ports=PORTS, host="127.0.0.1") -> list[int]`: ports where `socket.bind` fails
  - `compose(*args: str) -> subprocess.CompletedProcess`: `docker compose -f docker-compose.yml -f docker-compose.lab.yml <args>`, cwd `SERVER_DIR`
  - `healthy(base_url: str = BASE_URL, timeout: float = 3.0) -> bool`: GET `/api/public/health` returns 200
  - `runtime_ok() -> bool`: `uv` on PATH, or `python3 -c "import langfuse"` exits 0
  - `plugin_installed() -> bool`: `PLUGIN_ID` appears in `claude plugin list --json` output (any scope)
  - `api(env, method, path, body=None, base_url=BASE_URL) -> dict`: basic auth with public:secret keys, JSON in and out
  - `post_scores(env, payloads, api=api) -> list[str]`: POST each to `/api/public/scores`, collecting error strings and never raising
- `./lab langfuse up`: `docker_ok`, else "start Docker Desktop" and exit 1. Then `ensure_env`. If not already `healthy()`: check `port_conflicts()` (print the list and exit 1), run `compose("up", "-d")`, and poll `healthy()` every 3 s for up to 300 s. Print the URL, `LANGFUSE_INIT_USER_EMAIL` and the password.
  `down [--wipe]`: `compose("down")` or `compose("down", "-v")` after a `y/N` prompt. `status`: compose `ps`, `healthy`, `runtime_ok`, `plugin_installed`. `open`: URL and login.

- [ ] **Step 1: Write the failing tests:** `test_port_conflicts_detects_bound_port` (bind a socket to a free port, assert it's in `port_conflicts((port,))`, close it, assert it's no longer there). `test_docker_ok_false_for_missing_binary` (`docker_ok("no-such-docker-xyz")` is False). `test_healthy_false_when_nothing_listens` (`healthy("http://127.0.0.1:<free port>", 0.5)` is False). `test_post_scores_returns_errors_instead_of_raising` (an `api` stub raising `URLError` gives a list of 2 errors and no exception).
- [ ] **Step 2: Run.** Expected: FAIL (attributes missing).
- [ ] **Step 3: Implement** the helpers and `cmd_langfuse` as specified.
- [ ] **Step 4: Run** the unit tests. Expected: PASS. Then run `./lab check`. Expected: "All checks passed."
- [ ] **Step 5: Live check. The user must start Docker Desktop and agree to about 3–4 GB of image pulls first.** `./lab langfuse up`. Expected: healthy within 300 s (the first pull may take longer, so rerun `up`, which is idempotent). Then `python3 -c` using `lf.api(env, "GET", "/api/public/projects")` returns the `claude-code-lab` project. Log in at http://localhost:3000 with the printed credentials. `./lab langfuse status` shows every service running. If a service won't start without extra config (most likely `langfuse-ai-gateway`), disable it in `docker-compose.lab.yml` with `profiles: ["disabled"]` and record why for the README (spec: "upstream services stay as shipped unless one fails").
- [ ] **Step 6: Commit** with `feat(langfuse): ./lab langfuse up|down|status|open`.

### Task 4: `--trace` on `./lab new` and `./lab run`

**Files:**
- Modify: `lab` (`cmd_new`, `cmd_run`, the parsers, plus new `tracing_preflight` and `apply_tracing`)
- Test: `concepts/10-langfuse/tests/test_tracing.py`

**Interfaces:**
- Consumes: `lf.healthy`, `lf.runtime_ok`, `lf.ensure_env`, `lf.trace_tags`, `lf.plugin_env`, and `merge_json_file` in `lab`.
- Produces, in `lab`:
  - `tracing_preflight() -> dict[str, str]`: returns the `.env` values. Otherwise `die()` with `./lab langfuse up` (not healthy or no `.env`), or with uv install instructions (`curl -LsSf https://astral.sh/uv/install.sh | sh`) when `runtime_ok()` is False.
  - `enable_plugin(sandbox: Path, run=subprocess.run) -> str`: runs `claude plugin install <PLUGIN_ID> --scope local --json` with cwd `sandbox` and `stdin=DEVNULL`, and returns `"install"`. If that exits non-zero, it merges `{"enabledPlugins": {PLUGIN_ID: True}}` into `sandbox/.claude/settings.local.json` and returns `"settings"`.
  - `apply_tracing(sandbox: Path, env: dict, tags: str, enable=enable_plugin) -> dict[str, str]`: calls `enable`, merges `{"env": plugin_env}` into `settings.local.json`, and returns `plugin_env`.
- `--trace` flag on `new` and `run`. Tracing is on when `args.trace or meta(lab).get("trace")`. Preflight runs **before** `make_sandbox`. `cmd_run` builds tags per iteration with `ticket`, `model` (or `"default"`) and `run`, and passes `{**os.environ, **plugin_env}` as `env=` to the `claude` subprocess. `cmd_new` prints `traced → http://localhost:3000 (tags: …)`.

- [ ] **Step 1: Write the failing tests:** `test_apply_tracing_writes_env_and_returns_it` (temp sandbox with `.claude/settings.local.json` holding `{"claudeMdExcludes": ["x"]}`, a stub `enable` returning `"install"`: afterwards the file still has `claudeMdExcludes` and `env["CC_LANGFUSE_TRACE_TAGS"] == tags`, and the return value equals that env). `test_enable_plugin_falls_back_to_settings` (stub `run` returning exit code 1: returns `"settings"` and the file has `enabledPlugins[PLUGIN_ID] is True`). Import `lab` with `importlib.machinery.SourceFileLoader("lab", str(REPO / "lab"))`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** as specified.
- [ ] **Step 4: Run** the unit tests and `./lab check`. Expected: PASS.
- [ ] **Step 5: Live check (Langfuse up, uv installed with the user's consent).** `./lab new 01-single-agent --trace`. Expected: the sandbox's `.claude/settings.local.json` has the 5 env keys, and the plugin is enabled there. Note which method worked, `install` or `settings`. Then, **outside** any sandbox, from the repo root: `claude plugin list --json` shows the plugin **not enabled at user scope**. Also run `./lab new 01-single-agent` without `--trace`: no `env` block and no plugin.
- [ ] **Step 6: Commit** with `feat(lab): --trace enables the Langfuse plugin per sandbox`.

### Task 5: Acceptance scores and session link in `lab run --trace`

**Files:**
- Modify: `lablib/langfuse.py` (add `find_traces`, `trace_warning`), `lab` (`cmd_run` after acceptance)
- Test: `concepts/10-langfuse/tests/test_langfuse_helpers.py`

**Interfaces:**
- Consumes: `lf.score_payloads`, `lf.post_scores`, `lf.session_url`, `lf.api`.
- Produces:
  - `find_traces(env, session_id, timeout: float = 60, api=api, sleep=time.sleep) -> list[dict]`: polls `GET /api/public/traces?sessionId=<id>&limit=50` every 5 s until it gets a non-empty `data` or hits the timeout.
  - `trace_warning(session_id: str) -> str`: a message containing the session id and `HOOK_LOG`.
- In `cmd_run`, when traced and `session_id` exists: `traces = lf.find_traces(...)`. If there are none, print `lf.trace_warning`. Otherwise `errors = lf.post_scores(env, lf.score_payloads(session_id, accepted, len(regressions), acceptance_summary))`, then print `lf.session_url`. The record gains `langfuse_session_url`, `langfuse_traces` (a count) and `langfuse_errors`. The record is written whatever happens.

- [ ] **Step 1: Write the failing tests:** `test_find_traces_polls_until_data` (stub api returns `{"data": []}` then `{"data": [{"id": "t"}]}`, and a no-op `sleep`: returns 1 trace after 2 calls). `test_find_traces_times_out_empty` (always empty, timeout 0: returns `[]`). `test_trace_warning_mentions_hook_log`.
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** as specified.
- [ ] **Step 4: Run** the unit tests and `./lab check`. Expected: PASS.
- [ ] **Step 5: Live end-to-end:** `./lab run 01-single-agent --ticket T01 --model haiku --budget 0.5 --trace`. Expected: `✔ ACCEPTED`, `langfuse_traces >= 1`, a printed session URL that opens, `GET /api/public/traces?tags=lab:01-single-agent` non-empty with generations carrying token usage, and `GET /api/public/scores?name=accepted` containing this session. If session scores are rejected, implement the spec's fallback: attach to the newest trace of the session, using `traceId`. Then confirm a run **without** `--trace` creates no new traces (the trace count is unchanged).
- [ ] **Step 6: Commit** with `feat(lab): post acceptance scores to Langfuse on traced runs`.

### Task 6: Lab 10 content, docs and teardown

**Files:**
- Create: `concepts/10-langfuse/lab.json` (`"kind": "concept"`, `"trace": true`, `"run_prompt"` like A1's), `concepts/10-langfuse/overlay/.claude/settings.json` (the same allow rules as A1), `concepts/10-langfuse/README.md`
- Modify: `README.md` (one row in the concept table, plus a `--trace` line under "Running experiments"), `CLAUDE.md` (a layout line for `lablib/`)

**Interfaces:**
- Consumes: everything above. The README cites only behaviour observed in Tasks 3–5.

- [ ] **Step 1: Write** `lab.json` and the overlay settings. Run `./lab check`. Expected: lab 10 is listed, and its lint passes.
- [ ] **Step 2: Write the README** following the spec's outline (concept, setup, try it, testbed comparison, exercises, teardown), using `templates/lab/README.md` sections. Paste real output from the Task 5 live run (trace count, session URL shape, score), with the keys redacted.
- [ ] **Step 3: Update** the root `README.md` and `CLAUDE.md`. Run `./lab check`. Expected: "All checks passed."
- [ ] **Step 4: Teardown check:** `./lab langfuse down`, then `docker compose ps` (in `SERVER_DIR`, with both files) lists no running services, and `./lab langfuse status` reports Langfuse down.
- [ ] **Step 5: Commit** with `docs(langfuse): concepts/10-langfuse lab and README updates`.
