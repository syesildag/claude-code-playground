# A1: Single agent (control group)

> One agent in a ReAct loop (reason → act → observe) with the app's short CLAUDE.md. No subagents, no skills, no
> hooks. Every other architecture in this folder has to **beat this** on acceptance rate, cost or turns to justify
> its extra complexity.
> Course: AI Fluent 2 M2 ("default to a single agent"), AI Foundation M1.

## Why a control group
Multi-agent setups add latency, duplicate file reads in each context, and weaken prompt caching. They pay off only
for **context isolation, parallelism, very large scope, or independent review**. You only know whether they paid
off if you measure against a baseline on the same ticket, same model and same fresh sandbox.

## What's in this lab
Nothing extra: the app, its 5-line `CLAUDE.md`, the tickets, and allow rules for the test command.

## Try it
Interactively:
```bash
./lab new 01-single-agent    # then: cd into the sandbox && claude --setting-sources project,local
```
*"Implement tickets/T02-add-priority.md."* Watch how it explores, edits and verifies on its own.

As an experiment:
```bash
./lab run 01-single-agent --ticket T01 --model haiku
./lab run 01-single-agent --ticket T02 --model sonnet --repeat 3
./lab compare
```

## What to observe
- Did it read the ticket's "Context to read" files, or explore the whole repo?
- Did it run the tests before finishing? Did it respect "don't edit existing tests"?
- With `--repeat 3`: how much do turns and cost vary between identical runs? That noise is the bar any other
  architecture must clear.

## Exercises
1. Run all four tickets with Haiku, then with Sonnet. On which ticket does the smaller model fall short?
2. Compare against `architectures/02-planner-executor-verifier` on T03. Does the independent verifier catch what
   the single agent misses (temp files left behind after a failed save)?

## Takeaways
- Start here. Add an agent only when a measured limit (context, time, quality) justifies it.
