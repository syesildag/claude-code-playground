# Tickets: shared work items for every lab

Each ticket is an **AI-ready work item** with the five fields from the course (AI Fluent 1, Module 4):

| Field | Why it matters to an agent |
|---|---|
| **Goal** | A precise outcome ("return 401 for expired tokens"), not "fix the bug" |
| **Context to read** | Naming 3–5 files costs about 10k tokens. Letting the agent explore the whole repo costs far more |
| **Constraints** | What must not change. Agents take shortcuts (editing tests, `allow_failure`) unless told not to |
| **Acceptance criteria** | Checks a machine can run without asking you anything. Without them the agent has no finish line |
| **Out of scope** | Stops "helpful" scope creep |

| Ticket | Kind | What it exercises |
|---|---|---|
| [T01](T01-fix-done-counter.md) | bug, S | A failing test points at the bug. Stale docs (lab 01) can mislead the agent |
| [T02](T02-add-priority.md) | feature, M | Multi-file change, backward compatibility, CLI and API together |
| [T03](T03-atomic-save.md) | reliability, S | No existing test fails. The agent must reason about failure modes |
| [T04](T04-escape-html-export.md) | security, S | Every test is green today: "green tests" is not "correct" |

## Hidden acceptance tests (`acceptance/`)

`acceptance/test_tNN.py` turns each ticket's acceptance criteria into tests. They are **never copied into a
sandbox** while the agent works. `./lab run` copies them in only after the agent finishes, then runs them. That
makes them a fair, deterministic score for comparing architectures: the agent can't read them, edit them or
overfit to them.

`reference/TNN.patch` are known-good solutions. `./lab check` proves that each hidden test **fails on the baseline**
and **passes with its reference patch**, so the tests really measure the ticket.

## Writing a new ticket

1. Copy an existing ticket and keep all five sections.
2. Write `acceptance/test_tNN.py` against the public API described in the ticket. Only the ticket may define the
   interface, otherwise the test is unfair.
3. Solve it once in a sandbox, then save the diff as `reference/TNN.patch` (`git diff > ...`).
4. Run `./lab check`: the new ticket must fail on the baseline and pass with the patch.
