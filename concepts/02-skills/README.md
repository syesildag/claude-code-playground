# 02: Skills

> A skill is a folder with a `SKILL.md`: a repeatable procedure that loads **only when needed**. At session start
> Claude sees just each skill's name and description. The body loads when the skill triggers.
> Course: AI Fluent 1 M4 ("configure the project once"), AI Fluent 2 M4.

## The concept
- **The description is an activation condition, not documentation.** Say *what it does* and *when to use it*.
  Vague descriptions ("code tools") trigger unreliably.
- Who can invoke it: by default both you (`/name`) and Claude (automatically).
  `disable-model-invocation: true` means only you can. `user-invocable: false` means only Claude can.
- A skill can carry **supporting files** (templates, scripts), reached through `${CLAUDE_SKILL_DIR}`.
- `` !`command` `` runs a shell command **before** Claude sees the prompt and pastes in its output. That's live
  data at zero tool-call cost. A failing command aborts the skill, so make scripts exit 0.
- `context: fork` runs the skill in a subagent with its own context window, so only the summary comes back.
- Skills follow an open standard (agentskills.io). Old `.claude/commands/*.md` files still work, but skills
  replace them.

## What's in this lab
| Skill | Invocation | Demonstrates |
|---|---|---|
| `review-diff` | you **or** Claude | Description written as an activation condition; numbered steps; fixed output format; `allowed-tools` |
| `new-ticket` | **you only** (`disable-model-invocation`) | `$ARGUMENTS`, `argument-hint`, a supporting `template.md` via `${CLAUDE_SKILL_DIR}` |
| `project-status` | you or Claude | `` !`command` `` live data injection, bundled scripts that always exit 0 |
| `explain-module` | you or Claude | `context: fork` + `agent: Explore`: runs in an isolated read-only subagent |
| `taskboard-domain` | **Claude only** (`user-invocable: false`) | Background knowledge, auto-activated only for matching `paths:` |
| `/todo-scan` (`.claude/commands/`) | you or Claude | The legacy command format, for comparison |
| `extras/decoy-diff-summary/` | inactive | A competing skill for exercise 1 |

## Try it
```bash
./lab new 02-skills    # then: cd into the sandbox && claude --setting-sources project,local
```
1. Type `/` and look at the menu: `taskboard-domain` is missing because it's model-only.
2. Make a change (*"add a `--version` flag to the CLI"*), then say **"review the diff"**, without a slash.
   `review-diff` should trigger from its description alone.
3. `/new-ticket the CLI should support deleting a task`: a ticket appears in `tickets/`, following the template.
4. `/project-status`: the answer already knows the branch and test results. Press Ctrl+O and you'll see no
   `git` tool calls, because the data was injected before the prompt reached Claude.
5. `/explain-module taskboard/store.py`, then `/context`: the module's code was read in a fork, not in your session.
6. Ask *"why does stats() count by status the way it does?"* and see whether `taskboard-domain` gets loaded.

## What to observe
- **Ctrl+O** (transcript view) shows when a skill loads and what it ran.
- `/context`: skills cost only their description line until they trigger.
- Step 2 vs step 3: Claude invokes `review-diff` on its own. It can never invoke `new-ticket`.

## Exercises
1. **Break the trigger.** Copy `extras/decoy-diff-summary` into `.claude/skills/`, change `review-diff`'s
   description to `Code tool.`, start a new session and say "review the diff". Which skill wins now? Restore the
   description and try again. The course demo showed the same thing: a precise description beats a decoy.
2. **Inject more live data.** Add `` - Last change: !`git diff HEAD --stat` `` to `project-status`.
   Then add a command that fails (for example `` !`false` ``) and watch the whole skill abort.
3. **Turn a skill into a hook.** "Run the tests before finishing" as a skill can be ignored. Ask Claude to convert
   it into a `Stop` hook (lab 04 has one). That's the course's decision grid in practice.
4. **Write your own.** Use the `skill-creator` plugin, or just ask Claude: *"turn the prompt I keep typing for X
   into a skill"*. Read every bundled script before you trust it.

## Takeaways
- Skills turn prompts you keep retyping into a reviewed, versioned team asset ("the repetition tax").
- Cost model: about one description line per skill per session. The body loads on demand.
- A skill is still a suggestion. For "always, no exceptions", use a hook.
