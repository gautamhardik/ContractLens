# ContractLens: Workspace Guidelines & Agent Entry Point

This workspace is configured with a persistent, context-efficient agent memory system.

## 🎯 Task Execution Protocol
Future tasks must follow the bounded execution loop:
```
Read docs/agent-context/STATUS.md & FILE_MAP.md
           ↓
Identify minimum relevant files (Do NOT scan whole repo)
           ↓
Make focused changes adhering to .agents/rules/
           ↓
Run targeted validation
           ↓
Update docs/agent-context/ if durable facts changed (see CONTEXT_PROTOCOL.md)
           ↓
STOP
```

## 📚 Key Context Pointers
- **Mission & Constraints**: [`docs/agent-context/PROJECT.md`](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/PROJECT.md)
- **Current Status & Milestones**: [`docs/agent-context/STATUS.md`](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/STATUS.md)
- **Directory Orientation**: [`docs/agent-context/FILE_MAP.md`](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/FILE_MAP.md)
- **Architecture (Current vs Planned)**: [`docs/agent-context/ARCHITECTURE.md`](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/ARCHITECTURE.md)
- **Engineering Decisions**: [`docs/agent-context/DECISIONS.md`](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/DECISIONS.md)
- **Dataset Inventory**: [`docs/agent-context/DATASET.md`](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/DATASET.md)
- **Memory Protocol**: [`docs/agent-context/CONTEXT_PROTOCOL.md`](file:///c:/Users/hiten/Downloads/ContractLens/docs/agent-context/CONTEXT_PROTOCOL.md)

## ⚠️ Non-Negotiable Constraints
1. `Data/raw/` is strictly immutable. Never edit, move, or delete original PDFs.
2. Do not scan the entire repository recursively for routine tasks.
3. Keep code changes small, verified, and well-bounded.
4. Clean up transient files: Delete temporary scripts, intermediate generators, dead code, and caches (`__pycache__`, `.pytest_cache`) immediately after use to keep directories clean.
