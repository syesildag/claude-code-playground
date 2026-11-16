# T04: HTML export allows script injection

**Type:** security · **Size:** S

## Goal
`export_html()` inserts task titles into the page without escaping them. A task titled
`<script>alert(1)</script>` runs JavaScript when someone opens the exported board. Fix the injection.

## Context to read
- `taskboard/report.py`: `export_html()`
- `tests/test_report.py`

## Constraints
- Use the standard library (`html.escape`). No new dependencies.
- Keep the page structure: one `<li>` per task, with `class` set to the task status.

## Acceptance criteria
- [ ] A task titled `<script>alert(1)</script>` is rendered as `&lt;script&gt;alert(1)&lt;/script&gt;`. The raw `<script>` tag never appears in the output.
- [ ] `&` in a title is rendered as `&amp;`, and `"` as `&quot;`.
- [ ] The `title` argument of `export_html()` is escaped too.
- [ ] A regression test covers the escaping, and `python3 -m unittest` passes.

## Out of scope
- Styling and layout of the page.
