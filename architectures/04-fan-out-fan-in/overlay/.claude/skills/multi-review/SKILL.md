---
name: multi-review
description: Fan-out/fan-in review. Runs four specialist reviewers in parallel on a path, then consolidates their findings into work/review.md.
argument-hint: <path to review, default taskboard/>
disable-model-invocation: true
---

# Fan-out / fan-in review of `$ARGUMENTS`

If no path was given, review `taskboard/`.

```
            ┌─► bug-hunter ───────────┐
target ─────┼─► security-reviewer ────┼─► consolidator ─► work/review.md
 (fan-out)  ├─► performance-reviewer ─┤     (fan-in)
            └─► conventions-reviewer ─┘
```

1. **Fan out:** spawn all four reviewers **in one message, as parallel Agent calls**, each with the same
   instruction: "Review `<path>`." Don't review anything yourself.
2. **Collect** their outputs verbatim, each labelled with its reviewer name.
3. **Fan in:** spawn `consolidator` with all labelled findings and the target path.
4. Reply with the contents of `work/review.md`, nothing else.
