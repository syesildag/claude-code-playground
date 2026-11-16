---
paths:
  - "tests/**/*.py"
---

# Testing rules

These load only when Claude works on a test file.

- Use `unittest` only. No pytest, no third-party libraries.
- Each test gets its own `tempfile.TemporaryDirectory()`. Never read or write `./board.json`.
- One behaviour per test, named `test_<behaviour>`.
