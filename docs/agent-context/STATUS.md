# Project Status & Roadmap

Tracks milestone progress, active work, and anti-patterns ("Do Not Redo").

---

## Current Milestone
**Milestone 0: Agent Memory & Repository Setup** (Completed)

---

## Completed
- [x] Locked problem statement: PS4 — ContractLens.
- [x] Gathered initial real-world contract corpus (18 PDFs in `Data/raw/`).
- [x] Initialized Git repository tracking.
- [x] Established persistent agent memory and context system (`docs/agent-context/`).
- [x] Established behavioral agent rules (`.agents/rules/`).
- [x] Established domain task skills (`.agents/skills/`).

---

## In Progress
- None (Memory setup completed).

---

## Next Planned Milestones
1. **Corpus Audit**: Dedicated inspection of document categories, page counts, layout complexities, and amendment pairings.
2. **Ingestion & Extraction Strategy**: Select and benchmark PDF parser; implement layout- and page-preserving text extraction.
3. **Structured Entity & Obligation Pipeline**: Build extractors for contract parties, effective dates, obligations, and deadlines.
4. **Retrieval & Indexing Baseline**: Implement chunking, vector embeddings, and hybrid retrieval with page provenance.
5. **Agent Core & Tooling**: Build agent tools for deterministic lookup (dates, obligations, definitions) and grounded answering.
6. **User Interface**: Develop dashboard for document browsing, obligation calendars, and verifiable evidence display.
7. **Evaluation & Demo Preparation**: Benchmark on realistic contract queries; verify citation accuracy and risk detection.

---

## Do Not Redo
- **Do NOT reconsider or re-evaluate problem statement**: PS4 is locked.
- **Do NOT re-gather or re-download the raw corpus**: 18 documents already exist in `Data/raw/`.
- **Do NOT modify or delete raw documents in `Data/raw/`**: The folder is strictly immutable.
- **Do NOT re-scan the entire repository for general context**: Use `docs/agent-context/` instead.
