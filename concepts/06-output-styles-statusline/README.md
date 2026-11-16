# 06: Output styles & status line

> **Output styles** change *how Claude talks* for a whole session. The **status line** keeps the numbers that matter
> (model, context fill, cost) in front of you.
> Course: AI Foundation M2 (`/statusline`, `/context`), AI Fluent 1 M3 (cost awareness).

## The concept
- An output style is a Markdown file in `.claude/output-styles/` with frontmatter: `name`, `description`,
  `keep-coding-instructions`. Its text is sent **with every request** in the main session (not to subagents).
- `keep-coding-instructions: true` keeps Claude Code's built-in software-engineering guidance. Leave it out to turn
  Claude into something else entirely (a writing coach, a data analyst).
- Built-in styles: Default, Proactive, Concise, Explanatory, Learning. Switch with `/output-style <name>` (saved to
  `.claude/settings.local.json`).
- Choosing the right feature: *how it talks* is an output style. *What it knows* is CLAUDE.md. *A procedure* is a
  skill. *Must always happen* is a hook.
- The status line is any command: Claude Code pipes session JSON (`model`, `workspace`, `context_window`, `cost`,
  `rate_limits`…) to it on stdin and shows the first lines it prints.

## What's in this lab
| File | Demonstrates |
|---|---|
| `.claude/output-styles/socratic-tutor.md` | A teaching style: asks before telling, gives hints, writes code on request only |
| `.claude/output-styles/terse-reviewer.md` | A findings-only style: severity list with `file:line`, no preamble |
| `.claude/statusline.py` | `Haiku │ sandbox │ ⎇ main* │ ctx ▓▓░░░░░░░░ 18% │ $0.042 │ style: Socratic tutor` |
| `.claude/settings.json` | `statusLine` configuration |

## Try it
```bash
./lab new 06-output-styles-statusline    # then: cd into the sandbox && claude --setting-sources project,local
```
1. Look at the bottom of the screen: the status line is live. Watch `ctx` grow as you work.
2. `/output-style`: both custom styles are listed next to the built-ins (verified).
3. `/output-style Socratic tutor`, then *"Why does `taskboard stats` say 0 done?"* You should get a question back,
   not a fix.
4. `/output-style Terse reviewer`, then *"Review taskboard/report.py."*
5. `/output-style default` to go back.

## What to observe
- The same question gets very different answers. The model and code didn't change, only the instructions.
- The status line's `ctx` percentage: the course's "context drift" happens as it fills. Time for `/clear` or `/compact`.

## Exercises
1. **Your own style.** Write `.claude/output-styles/pair-programmer.md` that states a plan in one line before every
   edit. Restart Claude Code (style files are read at startup), then switch to it.
2. **Drop the coding instructions.** Set `keep-coding-instructions: false` on the tutor and ask it to fix a bug.
   What changes in how carefully it verifies its work?
3. **Status line upgrades.** Add `rate_limits.five_hour.used_percentage`, or turn the context bar red above 70%
   (ANSI colours are supported).
4. **Style vs skill.** The terse reviewer and lab 02's `review-diff` skill both review code. When would you use each?

## Takeaways
- Output styles are always-on instructions, so they cost tokens on every request. Keep them short.
- Keep cost and context visible: what you can't see, you can't manage.
