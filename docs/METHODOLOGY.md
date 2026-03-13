# Development Methodology

Pragmatic spec-driven development — plan before you build, but keep it proportional.

## Workflow

```
Requirements → Design → Tasks → Implement (repeat per feature)
```

Each phase produces a reviewable artifact before code is written. Work in small, iterative steps — not big upfront design.

## Project Files

| File | Purpose |
|------|---------|
| `requirements.md` | Testable acceptance criteria derived from the brief |
| `DECISIONS.md` | Architectural decisions with context and reasoning |
| `tasks.md` | Ordered work packages, ticked off as completed |
| `CLAUDE.md` | Persistent project context and rules for the AI agent |
| `OVERVIEW.md` | High-level system description and API surface |

## Principles

1. **Specs are proportional** — a bug fix gets a line item, a feature gets acceptance criteria. No over-formalization.
2. **Behaviour over implementation** — specs describe *what*, not *how*. Technical detail goes in `DECISIONS.md`.
3. **Small steps, verified** — implement one task, verify it works, move on. Don't batch.
4. **Decisions are logged** — every non-obvious choice gets a `DECISIONS.md` entry with context, reasoning, and trade-offs.
5. **Verify, don't trust** — review AI output at each step. Specs guide the agent, they don't guarantee correctness.
6. **Minimal markdown** — if the doc is harder to review than the code, it's too verbose.
