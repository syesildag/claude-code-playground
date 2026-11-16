# A3: Sequential pipeline

> Each agent produces an **artifact** that becomes the next agent's input. The developer receives a clean spec, not
> the noisy ticket discussion, and a human validates the artifact between stages.
> Course: AI Fluent 2 M2 (pattern 1).

## The architecture
```
ticket ─► spec-writer ─► work/spec.md ─► 👤 checkpoint ─► developer ─► taskboard/ ─► test-writer ─► tests/
          (writes work/ only)                          (writes taskboard/ only)  (writes tests/ only)
```
- **Least privilege per role:** a `scoped_writes.py` hook in each agent's frontmatter fences its writes. The
  developer *cannot* edit tests, so "make it green by changing the test" is impossible by construction.
- **A hard precondition:** the developer refuses to start without `work/spec.md`. The course demo showed an agent
  that started anyway. Here, test whether your model honours the refusal.
- **Human control per step:** the most control of all the patterns, and the slowest.
- **Cost caveat:** each stage re-reads the files it needs in its own context. On a small ticket this costs *more*
  than a single agent.

## Try it
```bash
./lab new 03-sequential-pipeline    # then: cd into the sandbox && claude --setting-sources project,local
```
1. `/pipeline tickets/T02-add-priority.md`, read the spec at the checkpoint, and request one change.
2. Precondition test: delete `work/spec.md` and ask *"use the developer agent to implement the spec"*. It should
   answer `NO SPEC: stopping`.
3. Headless (the checkpoint is skipped with `--auto`): `./lab run 03-sequential-pipeline --ticket T02`

## What to observe
- `work/spec.md`: is it good enough that the developer never needs the ticket?
- Hook denials in Ctrl+O if a role strays outside its directory.
- Whether the test writer finds bugs the developer introduced, or just writes tests that pass.

## Exercises
1. **TDD variant.** Reorder the skill to spec → test-writer → developer. Tests are written against the spec before
   the code exists. Does the acceptance rate change on T02?
2. **Pipeline vs single agent.** `./lab compare --ticket T02`: is the extra cost buying quality?
3. **Data migration example** (from the course exercise): write a ticket for "migrate board.json to add a `version`
   field, with a rollback script". Why is it sequential by nature?

## Takeaways
- Use a pipeline when each stage's output can be reviewed on its own (specs, migrations, release steps).
- Artifacts in files are auditable, resumable and diffable, which conversation history isn't.
