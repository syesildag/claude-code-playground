---
name: explain-module
description: Explain how one module of the taskboard package works, for a developer new to the code. Use when asked to explain, walk through or summarize a file or module.
argument-hint: <path, e.g. taskboard/store.py>
context: fork
agent: Explore
background: false
---

Explain `$ARGUMENTS` to a developer who is new to this codebase.

Read the file, then follow its imports and its callers (grep for its public names) one level deep.
Return, in this order and in under 250 words:

1. **Purpose**: one sentence.
2. **Public API**: each function or class, with one line on what it does.
3. **Collaborators**: what calls it and what it calls.
4. **Gotchas**: surprising behaviour, edge cases or likely bugs, each with `file:line`.
