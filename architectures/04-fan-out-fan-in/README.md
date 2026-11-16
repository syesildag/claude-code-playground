# A4: Fan-out / fan-in review

> The same starting context goes to several specialists **in parallel**, each with a narrow perspective. A
> consolidator deduplicates and ranks their findings. Typical result: 20–30 overlapping findings become about 10
> prioritized ones.
> Course: AI Fluent 2 M2 (pattern 2), AI Fluent 2 M1 ("prefer small specialized verifiers").

## The architecture
```
            ┌─► bug-hunter (sonnet) ──────────┐
taskboard/ ─┼─► security-reviewer (sonnet) ───┼─► consolidator (sonnet) ─► work/review.md
 fan-out    ├─► performance-reviewer (haiku) ─┤    dedupe · verify · rank
            └─► conventions-reviewer (haiku) ─┘
```
- **Wall-clock time** is roughly that of the slowest reviewer. **Token burn rate** is about four times higher, so
  subscription quotas run out faster.
- Every reviewer uses the **same line format**, which is what makes consolidation mechanical.
- Models are routed by difficulty: judgment-heavy perspectives on Sonnet, pattern-spotting on Haiku.
- Fan-out suits **analysis and review**. Parallel *code generation* only works when the parts are truly independent.

## A measurable comparison
The app has five planted review targets. `scripts/score_review.py` checks a review for each of them:
the T01 counter bug, the T04 XSS, the T03 non-atomic save, the N+1 reload in `cli list`, and the missing type
hints on `export_html` (a rule in `docs/conventions.md`).

```bash
./lab new 04-fan-out-fan-in && cd .sandbox/04-fan-out-fan-in-*
bash scripts/compare-reviews.sh          # runs /single-review, then /multi-review, scores both (about $1–3 on Sonnet)
```
It reports, for each style: wall time, turns, total cost, cost per model, and `recall: N/5`.

## Try it interactively
```bash
claude --setting-sources project,local
```
1. `/multi-review taskboard/`. In Ctrl+O you should see four reviewers start in the same turn.
2. `/single-review taskboard/`, then compare the two files in `work/`.
3. `python3 scripts/score_review.py work/review.md`

## Exercises
1. **Does specialization pay?** Run `compare-reviews.sh` three times (the results are non-deterministic). Is
   fan-out's recall consistently higher? Is it worth the cost?
2. **Cheaper fan-out.** Set every reviewer to `model: haiku`. What happens to recall, and to cost?
3. **Objective signals.** The course advice: for security, run a real analysis tool and let the LLM interpret its
   report. Add `python3 -m py_compile` or a `grep` for `shell=True` to the security reviewer as a first step.
4. **Translate a README into 3 languages.** Write a fan-out skill for it. Why does it need no consolidator?

## Takeaways
- Parallel specialists with a strict output contract plus one consolidator work better than one overloaded
  generalist, when the measurements say so.
- Watch the burn rate: parallel agents spend your quota faster per minute.
