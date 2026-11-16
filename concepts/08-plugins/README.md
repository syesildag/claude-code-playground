# 08: Plugins & marketplaces

> Lab 02–04 artifacts live in one repo. Copy them into five repos and you get five drifting versions. A **plugin**
> bundles skills, agents, hooks, MCP servers and output styles into one **versioned** unit. A **marketplace** is just a
> repo with a catalog file.
> Course: AI Fluent 1 M5 ("publish once: the team installs it, the org enforces it"), M6 / AI Fluent 2 M6.

## The concept
- **Plugin layout:** `.claude-plugin/plugin.json` (name, version, …) plus `skills/`, `agents/`, `hooks/hooks.json`,
  `.mcp.json`, `output-styles/` at the plugin root.
- **Namespacing:** components are prefixed with the plugin name (`/review-kit:review`, `review-kit:reviewer`), so
  two plugins never collide.
- **`${CLAUDE_PLUGIN_ROOT}`** points to the installed copy. Use it in hook commands and MCP args.
- **Marketplace:** `.claude-plugin/marketplace.json` lists plugins and where to fetch them (a relative path, GitHub,
  git URL, npm…). It stays inside your organization.
- **Ways to load a plugin:** for one session, `--plugin-dir <path>` (nothing installed). Personally,
  `/plugin marketplace add` + `/plugin install`. For a team, commit `extraKnownMarketplaces` + `enabledPlugins` in
  `.claude/settings.json`, and anyone who clones the repo is offered the plugin.
- Plugin hooks are **policies that travel with the install**: deterministic and free (no tokens).

## What's in this lab
| Path (in the sandbox) | Role |
|---|---|
| `marketplace/.claude-plugin/marketplace.json` | Catalog `lab-tools` with one entry |
| `marketplace/plugins/review-kit/.claude-plugin/plugin.json` | Manifest, version `1.0.0` |
| `…/skills/review/SKILL.md` | `/review-kit:review` |
| `…/agents/reviewer.md` | `review-kit:reviewer`, read-only, Sonnet |
| `…/hooks/hooks.json` + `scripts/block_sql_drop.py` | Policy: no `DROP TABLE` / `TRUNCATE` from any session |
| `team-settings.example.json` | How a team repo would enable the plugin for everyone |

## Try it
```bash
./lab new 08-plugins
cd .sandbox/08-plugins-*
claude plugin validate ./marketplace                     # ✔ Validation passed
claude --setting-sources project,local --plugin-dir ./marketplace/plugins/review-kit
```
1. `/plugin` (or `/agents`, or type `/review`): the plugin's components appear with the `review-kit:` prefix.
2. *"Run `sqlite3 board.db 'DROP TABLE tasks'`."* The plugin's hook blocks it. Verified result:
   *"The `DROP TABLE tasks` was blocked by a PreToolUse hook from the review-kit plugin."*
3. Change something, then `/review-kit:review`. The skill delegates a second opinion to `review-kit:reviewer`.
4. `claude plugin details review-kit` (after installing, below) shows the inventory and the estimated token cost.

## Install it for real (optional: it changes your user config)
```bash
claude plugin marketplace add ./marketplace      # registers "lab-tools" in your user config
claude plugin install review-kit@lab-tools
claude plugin list
# undo:
claude plugin uninstall review-kit@lab-tools && claude plugin marketplace remove lab-tools
```

## Exercises
1. **Ship a fix.** Add a secrets check to the `review` skill, bump `version` to `1.1.0` in `plugin.json`, and add a
   changelog line. Run `claude plugin update review-kit@lab-tools`. Never change a published version in place.
2. **Team rollout.** Fill in the absolute path in `team-settings.example.json`, merge it into
   `.claude/settings.json`, and start a new session without `--plugin-dir`. You get offered the plugin.
3. **Add an MCP server to the plugin.** Move lab 07's server into `review-kit/` with a `.mcp.json` that uses
   `${CLAUDE_PLUGIN_ROOT}`. One install now brings tools too.
4. **Promote an artifact.** Take lab 02's `review-diff` skill up the course's maturity ladder: experimental (in one
   repo), then cataloged (in this marketplace, with an owner), then published (semver ≥ 1.0, used by 2+ teams,
   changelog).
5. **Audit before trust.** Pick a public plugin, read every script and hook it ships, then answer: what can it
   run on your machine?

## Takeaways
- Distribution first, then governance (hooks and settings as policy), then automation (lab 09). Automating before
  you can distribute and govern means finding problems in production.
- Pin versions. Disable the plugins you don't need, because each one costs context.
- Installing a plugin means trusting all of its code. Mirror and review external plugins internally.
