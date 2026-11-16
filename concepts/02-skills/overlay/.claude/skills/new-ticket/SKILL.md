---
name: new-ticket
description: Create a new AI-ready ticket in tickets/ with goal, context, constraints, testable acceptance criteria and out-of-scope sections.
argument-hint: <what needs to change>
disable-model-invocation: true
allowed-tools: Read Glob Grep Write
---

Create a ticket for: **$ARGUMENTS**

1. Find the next free number: list `tickets/T*.md`, take the highest `NN` and add one.
2. Read the template at `${CLAUDE_SKILL_DIR}/template.md`, then read the code the change touches. You need to
   name the exact files under "Context to read" (3 to 5 files, not the whole package).
3. Write acceptance criteria that **a machine can check without asking a human**: concrete inputs and expected
   outputs, return values, exit codes. "Works correctly" and "code is clean" are not criteria.
   If you can't make a criterion testable, ask the user **one** question instead of guessing.
4. Write `tickets/TNN-<kebab-case-slug>.md` from the template.
5. Reply with the file path and the acceptance criteria only.
