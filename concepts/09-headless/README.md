# 09: Headless mode & CI

> `claude -p` runs Claude without the terminal UI: one prompt in, a result out. That's how agents run in scripts,
> pipelines and this repo's own `./lab run`.
> Course: AI Fluent 1 M5 (headless CI), AI Fluent 2 M7 (LLMOps: trace, monitor, evaluate).

## The concept
| Flag | Why it matters headless |
|---|---|
| `--output-format json` | One JSON object at the end: `result`, `total_cost_usd`, `num_turns`, `modelUsage` (cost **per model**), `permission_denials`, `session_id` |
| `--output-format stream-json --verbose` | One event per line as it happens, the raw material for tracing |
| `--json-schema '<schema>'` | The final answer is validated against your schema and returned in `structured_output` |
| `--tools "Read,Grep,Glob"` | Only these built-in tools *exist*, so the run is read-only by construction |
| `--permission-prompts none` | Anything that would prompt is denied (nobody is there to answer) |
| `--max-budget-usd 0.25` | Hard spending cap per run |
| `--setting-sources project,local` | Ignore personal `~/.claude` settings: reproducible across machines |
| `--settings '{…}'` | Inject settings (such as allow rules) for this run only. Honoured even in an untrusted workspace |

Two gotchas we hit while building this lab:
- **Untrusted workspace:** allow rules from `.claude/settings.json` are ignored until someone accepts the trust
  dialog, even with `-p`. Use `--settings` (or trust the folder once interactively).
- **stdin:** `claude -p` waits 3 seconds for piped input. In scripts, add `< /dev/null`.

## What's in this lab
| File | Demonstrates |
|---|---|
| `scripts/headless-review.sh` | Read-only (`--tools`), budget-capped review with `--json-schema`. Exits 1 on `request_changes`, a CI gate |
| `schemas/review.schema.json`, `prompts/review.md` | The output contract and the prompt template |
| `scripts/print_review.py` | Reads `structured_output` and turns the verdict into an exit code |
| `scripts/trace.py` | Live trace from `stream-json`: each tool call, errors, cost, cache reads/writes, files read twice |
| `.github/workflows/claude-review.yml` | The same gate in GitHub Actions (example: needs an API key secret) |

## Try it
```bash
./lab new 09-headless && cd .sandbox/09-headless-*
bash scripts/headless-review.sh taskboard/report.py; echo "exit=$?"
```
Verified output (Haiku, about $0.13):
```
✘ [blocking] taskboard/report.py:5: Task titles are interpolated into the HTML list without escaping … stored XSS …
✘ [blocking] taskboard/report.py:8: The `title` parameter … is interpolated unescaped into <title> …
⚠ [minor] taskboard/report.py:5: `t.status` is written unescaped into the class attribute …
verdict: request_changes · turns 5 · cost $0.1296
exit=1
```
Then trace an agent at work:
```bash
python3 scripts/trace.py "Fix the bug in tickets/T01-fix-done-counter.md, then run the tests once." --model haiku
```
```
   4.7s  tool   Bash     cat tickets/T01-fix-done-counter.md && …
  11.3s  tool   Edit     …/taskboard/service.py
  13.2s  tool   Bash     python3 -m unittest 2>&1 | tail -20
  17.3s  done   turns=8 cost=$0.0073 cache_read=210659 cache_write=18845
```

## What to observe
- `cache_read` vs `cache_write`: prompt caching at work. Most input tokens are cache reads, which cost far less.
- `modelUsage` in the JSON output: how much each model cost, which is how you check that routing works.
- `permission_denials`: an audit trail of what the agent tried and was refused.

## Exercises
1. **Swap the model.** `MODEL=sonnet bash scripts/headless-review.sh taskboard/store.py`. Does it flag the
   non-atomic save (T03)? What does it cost compared with Haiku?
2. **Deterministic first.** In the workflow, the unit tests run *before* the LLM review. Why is that order cheaper?
3. **Spot waste.** Run `trace.py` on ticket T02 and look for files read more than once. Add a "Context to read"
   hint to the prompt and run it again.
4. **Resume.** Take `session_id` from a JSON result and run `claude -p --resume <id> "now add a test"`.
5. **Build on it.** `./lab run` (repo root) is this lab's techniques assembled into an experiment runner. Read
   `cmd_run` in `lab`.

## Takeaways
- Headless runs need explicit limits: tools, budget, permissions, settings sources.
- Structured output turns an LLM opinion into something a pipeline can branch on. Let deterministic gates run first.
- Measure (cost, turns, cache, denials) before you optimize.
