---
name: frontend-ui
description: Guidelines for developing the ContractLens user interface and dashboard.
---

# Frontend UI Skill

## When to Use
Use when implementing user interfaces, dashboard views, contract viewers, obligation timelines, or evidence sidebars.

## Critical Constraints
1. **Status**: No frontend currently exists in the repository.
2. **Decision Pre-requisite**: Confirm framework selection in `docs/agent-context/DECISIONS.md` before generating scaffolding.
3. **Evidence-First UX**:
   - The UI must emphasize side-by-side or split-pane evidence display: user sees both the agent's summary and the highlighted clause in the original contract text/PDF.
4. **Performance & Cleanliness**:
   - Avoid heavy or redundant dependencies. Focus on clarity, responsive layout, and intuitive exploration of dense legal data.

## Typical Workflow
1. Verify decided frontend stack in `DECISIONS.md`.
2. Implement components for contract portfolio, obligation calendar/list, and grounded chat/Q&A.
3. Verify interactive flows and document citation linking.
