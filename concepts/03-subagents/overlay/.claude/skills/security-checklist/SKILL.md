---
name: security-checklist
description: Security review checklist for this Python codebase (output encoding, file writes, secrets, deserialization, subprocess). Preloaded by the security-reviewer agent; use it for any security review.
user-invocable: false
---

# Security checklist

1. **Output encoding**: user text placed in HTML goes through `html.escape` (titles and attributes).
2. **File writes**: are writes atomic (temp file + `os.replace`)? Can a user-supplied path escape its directory?
3. **Secrets**: no keys, tokens or passwords in code, tests or fixtures. `.env` is gitignored.
4. **Deserialization**: JSON only. No `pickle`, `eval`, `exec` or `yaml.load` on user data.
5. **Subprocess**: no `shell=True` with user-controlled input.
6. **Error output**: messages to users don't leak stack traces or absolute paths.
7. **Data loss**: can any failure path truncate or delete user data?
