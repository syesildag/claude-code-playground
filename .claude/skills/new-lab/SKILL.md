---
name: new-lab
description: Create a new lab in this repository (a concept example or an agent-architecture example), from scaffold to a passing ./lab check. Use when the user wants to add an example, lab, exercise or architecture to the playground.
argument-hint: <what the lab should teach>
allowed-tools: Bash(./lab scaffold *) Bash(./lab check) Bash(./lab list) Bash(./lab new *)
---

# Create a lab: $ARGUMENTS

1. **Decide the kind.** A *concept* teaches one Claude Code building block (`concepts/`). An *architecture* is a
   multi-agent pattern you can measure on tickets (`architectures/`). Pick the next free number from `./lab list`.
2. **Scaffold:** `./lab scaffold <concepts|architectures> NN-kebab-name`.
3. **Build the overlay.** Files in `overlay/` are copied on top of `app/` in every sandbox. Follow the conventions in
   the root `CLAUDE.md`: stdlib Python, hooks via `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/x.py"`, explicit
   `tools` and `model` on agents, descriptions that say *what* and *when*.
4. **Test the scripts.** Every hook or script gets offline tests in `<lab>/tests/` (JSON in, exit code and stdout
   out). See `concepts/04-hooks/tests/test_hooks.py`.
5. **Write the README** from `templates/lab/README.md`: concept, what's in the lab, try it (exact prompts), what to
   observe, exercises, takeaways. For architectures, set `run_prompt` in `lab.json` so `./lab run` works.
6. **Verify:** `./lab check` must pass. Then `./lab new <lab>` and try the README's first prompt for real.
7. Add the lab to the table in the root `README.md`.
