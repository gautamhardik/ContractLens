# Context Update Protocol

Protocol for maintaining persistent project memory and preventing context staleness or bloating.

---

## When to Update Context Files

Update persistent memory files **only** when durable, project-level facts change:
1. **Architecture Changes**: A new service, layer, or major directory is introduced (`ARCHITECTURE.md`, `FILE_MAP.md`).
2. **Milestone Progress**: A milestone is started or completed (`STATUS.md`).
3. **Decisions Finalized**: A previously undecided technology choice is locked (e.g., embedding model, vector DB, framework) (`DECISIONS.md`).
4. **Dataset Changes**: New raw or benchmark datasets are added or structured (`DATASET.md`).
5. **Project Constraints or Scope**: Problem statement or hackathon parameters evolve (`PROJECT.md`).

---

## What NOT to Put in Context Files

Do **not** update memory files for:
- Minor, routine code edits or syntax tweaks.
- Temporary debugging notes, logs, or error traces.
- Individual function implementations or internal variables.
- Verbatim copies of source code or complete PDF text.
- Speculative designs that have not been agreed upon.

---

## File Responsibilities (Separation of Concerns)

Maintain strict separation across memory files to avoid bloat and redundant maintenance:
- **`PROJECT.md`** → **WHAT** the product is (identity, mission, problem statement).
- **`ARCHITECTURE.md`** → **HOW** systems connect (current vs. planned layers and pipelines).
- **`FILE_MAP.md`** → **WHERE** files live (top-level folders, entry points, planned locations).
- **`DECISIONS.md`** → **WHY** specific architectural choices were accepted or left undecided.
- **`STATUS.md`** → **WHAT STAGE** the project is at (completed, in progress, next, do-not-redo).
- **`DATASET.md`** → **WHAT DATA** exists (raw corpus inventory, formats, immutability rules).
- **`CONTEXT_PROTOCOL.md`** → **HOW MEMORY** is maintained (this document).
- **`.agents/rules/`** → **HOW THE AGENT BEHAVES** (always-on developer conduct).
- **`.agents/skills/`** → **HOW TO EXECUTE SPECIFIC TASKS** (on-demand technical playbooks).

---

## Maintenance Rule
If an agent discovers that a context document contains outdated information:
1. Verify the reality in the active codebase.
2. Update the corresponding context file concisely.
3. Never scan the entire repository to compensate for an outdated context document.
