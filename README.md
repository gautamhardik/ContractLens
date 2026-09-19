# ContractLens — Business Contract Review & Obligation Tracking Agent

> **Hackathon 2026 | Problem Statement 4 (PS4)**

ContractLens transforms static commercial contracts into structured, queryable operational intelligence with verifiable source citations and page-level evidence.

---

## ⚡ Agent Quickstart (Read First)
Before starting any task, consult persistent memory to minimize token usage:
1. **[PROJECT.md](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/PROJECT.md)**: Product mission, core capabilities, and constraints.
2. **[STATUS.md](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/STATUS.md)**: Current roadmap milestone and "Do Not Redo" anti-patterns.
3. **[DECISIONS.md](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/DECISIONS.md)**: Accepted decisions vs. undecided choices.
4. **[FILE_MAP.md](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/FILE_MAP.md)**: Repository structure and file orientation.
5. **[DATASET.md](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/DATASET.md)**: Corpus inventory (18 raw immutable contract PDFs).

Operational rules are located in [`.agents/rules/`](file:///c:/Users/hiten/Downloads/ContractLens/.agents/rules/) and task-specific playbooks in [`.agents/skills/`](file:///c:/Users/hiten/Downloads/ContractLens/.agents/skills/).

---

## Repository Structure
```
ContractLens/
├── .agents/
│   ├── rules/                 # Always-on behavior rules
│   └── skills/                # Task-specific workflows (Ingestion, RAG, Agent, UI, Testing)
├── Data/
│   └── raw/                   # 18 Immutable commercial contract PDFs
├── docs/
│   └── agent-context/         # Persistent compact memory
├── .gitignore
└── README.md
```

## Current Milestone
**Milestone 0 Complete** — Persistent agent memory established.  
**Next**: Non-destructive corpus audit of `Data/raw/` to benchmark parser feasibility.
