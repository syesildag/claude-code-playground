# review-kit

A small team plugin from the Claude Code lab marketplace. It ships three things together, so every repository that
enables it gets the same versions:

- **Skill** `/review-kit:review`: five-point review of the current diff (correctness, tests, security,
  conventions, scope) with an APPROVE or REQUEST CHANGES verdict.
- **Agent** `review-kit:reviewer`: an independent, read-only reviewer that runs in a fresh context.
- **Hook policy**: blocks `DROP TABLE`, `DROP DATABASE` and `TRUNCATE TABLE` in any shell command, in every session
  where the plugin is enabled. It costs zero tokens and gives the model no say.

Install from this lab's local marketplace:

```
/plugin marketplace add ./marketplace
/plugin install review-kit@lab-tools
```

Changelog: 1.0.0, first release.
