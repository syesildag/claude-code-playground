# 04: Hooks, deterministic gates

> An instruction in CLAUDE.md is an *intention* the model may ignore. A hook is a program that **Claude Code runs**
> at a lifecycle event. It doesn't depend on the model agreeing.
> Course: AI Fluent 1 M1 (gates, secret scanning), M4–M5, AI Foundation M4.

## The concept
Three levels of control, from the course:

| Level | Mechanism | Guarantee |
|---|---|---|
| 1. Instruction | A line in CLAUDE.md | None. Diluted in the context and ignorable |
| 2. Re-injection | A hook that adds the rule back at the right moment (`additionalContext`) | Better odds, still probabilistic |
| 3. Gate | A hook that **blocks** (exit 2, `deny`, `decision: block`) or a script, test or CI check | Deterministic |

**The hook contract:** the event arrives as JSON on stdin. Your script answers with an exit code and an optional
JSON object on stdout.
- `exit 0` + nothing printed = no opinion. `exit 2` = block, and **stderr** becomes the reason. Any other code is
  a non-blocking error (the action proceeds!), so use exit 2 when you mean to enforce something.
- Richer answers come back as JSON: `permissionDecision: allow|deny|ask` (PreToolUse),
  `decision: "block"` + `reason` (Stop, PostToolUse, UserPromptSubmit), `additionalContext` (inject text).
- `matcher` filters by tool name (`Edit|Write`). `if` filters by a permission-rule pattern (`Bash(git commit*)`).
- A hook runs at zero token cost. Hooks load at session start, so restart after editing them (the course demo hit
  exactly this).

## What's in this lab
| Event | Script | Style | What it does |
|---|---|---|---|
| SessionStart (startup) | `session_context.py` | `additionalContext` | Gives Claude branch, dirty files and test status at launch |
| SessionStart (compact) | `reinject_rules.py` | `additionalContext` | Re-injects `.claude/critical-rules.md` after compaction (level 2) |
| UserPromptSubmit | `prompt_guard.py` | `decision: block` / context | Blocks prompts containing secrets. Attaches the ticket when you mention `T01` |
| PreToolUse (Bash) | `block_dangerous_bash.py` | JSON `deny` | `rm -rf`, force push, `--no-verify`, `reset --hard`, `DROP TABLE`, `curl \| sh` |
| PreToolUse (Bash, `if: git commit*`) | `scan_secrets.py` | exit 2 | Scans what's about to be committed for keys and `.env` files |
| PreToolUse (Edit\|Write) | `protect_files.py` | exit 2 | Existing tests and `.env*` are read-only. *New* tests are allowed |
| PostToolUse (Edit\|Write) | `check_python.py` | `decision: block` | Compiles each edited `.py` and feeds errors straight back |
| Stop | `stop_gate_tests.py` | `decision: block` | **Claude can't finish while tests are red** (respects `stop_hook_active`) |
| every event | `log_event.py` | silent | Writes the agent loop to `.claude/logs/events.log` |

Also: `scripts/install-git-hook.sh` installs the same secret scanner as a real **git** pre-commit hook (layer two),
and `tests/test_hooks.py` (in this lab folder, not the sandbox) shows how to unit-test hooks without Claude.

## Try it
```bash
./lab new 04-hooks
cd .sandbox/04-hooks-*
tail -f .claude/logs/events.log &          # watch the loop
claude --setting-sources project,local
```
1. *"What branch are we on and are the tests green? Don't use tools."* The answer comes from `SessionStart`.
2. *"Run `rm -rf build`."* Denied, and Claude explains why. This is verified behaviour:
   ```
   13:04:45  SessionStart      startup
   13:04:46  UserPromptSubmit  Run rm -rf build …
   13:04:49  PreToolUse        Bash       rm -rf build      ← denied by block_dangerous_bash.py
   13:04:51  Stop              stop_hook_active=False
   ```
3. *"Make test_stats_counts_done_tasks pass by editing the test."* `protect_files.py` refuses, and Claude has to fix
   `service.py` instead.
4. *"Add a comment to taskboard/service.py and stop."* The Stop gate runs the tests, sees the T01 failure, and
   sends Claude back to work. Watch for `stop_hook_active=True` in the log on the second stop.
5. `echo 'AWS="AKIA'"$(printf 'A%.0s' {1..16})"'"' > leak.py`, then *"commit everything"*. `scan_secrets.py` blocks it.
6. Paste a fake key into your prompt: `sk-ant-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`. The prompt never reaches the model.

## What to observe
- `events.log`: the ReAct loop made visible (prompt → tool → result → stop). `events.jsonl` has each event's full
  JSON. It's the best way to learn the schemas.
- Ctrl+O: hook feedback appears in the transcript (`Stop hook feedback`, denial reasons).
- `/hooks` lists every configured hook and where it came from.

## Exercises
1. **Bypass the git layer.** Run `bash scripts/install-git-hook.sh`, then ask Claude to commit with `--no-verify`.
   Which layer stops it? Why does the course say the real last line is CI?
2. **Turn level 1 into level 3.** Pick a rule from `critical-rules.md` and enforce it with a hook instead.
3. **A prompt-based hook.** Add a model-evaluated check next to the command hook in `Stop`:
   ```json
   { "type": "prompt", "prompt": "Did the assistant run the test suite after its last code change? $ARGUMENTS Reply {\"ok\": true} or {\"ok\": false, \"reason\": \"...\"}." }
   ```
   It's cheaper to write, but probabilistic and token-costly. When would you accept that trade?
4. **Fail open vs fail closed.** Make `block_dangerous_bash.py` crash (add `1/0`). Does the command run? (Exit 1 is
   non-blocking.) How would you make a security hook fail closed?
5. **Measure the gate.** Run `./lab run 04-hooks --ticket T01` and `./lab run 01-single-agent --ticket T01`, then
   `./lab compare`. Does the Stop gate change acceptance or turns?

## Takeaways
- Never write an LLM instruction for something a script can enforce: the script is cheaper, more reliable, and
  the responsibility stays with you.
- Hooks are code: version them, review them, test them (see `tests/test_hooks.py`).
- Layer your defences: Claude hook, then git hook, then CI. Each one can be bypassed on its own.
