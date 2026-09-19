# File Map

Quick orientation map for the ContractLens repository. Consult this map to determine where files live before navigating or modifying code.

## Root Directory
- `.agents/`: Agent configuration, operational rules, and task-specific skills.
- `docs/agent-context/`: Persistent compact memory and context protocol for agents.
- `Data/`: Project dataset storage.

## Data Layer
- `Data/raw/`: Original, immutable contract corpus (18 PDF agreements/amendments).
- *Planned:* `Data/processed/`: Extracted text, parsed chunks, and intermediate representations.

## Backend (Planned)
- Path: *Not yet established.*
- Expected Purpose: Ingestion pipeline, parsing, vector indexing, agent orchestration, and API endpoints.

## Frontend (Planned)
- Path: *Not yet established.*
- Expected Purpose: User interface for contract review, obligation tracking, and evidence inspection.

## Tests (Planned)
- Path: *Not yet established.*
- Expected Purpose: Unit and integration tests for extraction, indexing, and tool execution.

## Scripts / Notebooks (Planned)
- Path: *Not yet established.*
- Expected Purpose: Ad-hoc corpus audit, evaluation benchmarks, or batch ingestion scripts.
