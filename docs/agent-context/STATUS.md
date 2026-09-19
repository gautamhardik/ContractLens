# Project Status & Roadmap

Tracks milestone progress, active work, and anti-patterns ("Do Not Redo").

---

## Current Milestone
**Phase 0: Agent/Project Context & Master Plan Alignment** (Completed)

---

## Completed
- [x] Locked problem statement: PS4 — ContractLens.
- [x] Gathered initial real-world contract corpus (18 PDFs in `Data/raw/`).
- [x] Initialized Git repository tracking.
- [x] Established persistent agent memory and context system (`docs/agent-context/`).
- [x] Established behavioral agent rules (`.agents/rules/`).
- [x] Established domain task skills (`.agents/skills/`).
- [x] Established root orientation files (`AGENTS.md`, `README.md`, `.gitignore`).
- [x] Established Evaluation Framework & Benchmark criteria (`EVALUATION.md`).
- [x] Aligned master architecture and phased roadmap with Master Directive.
- [x] **Phase 1 — Corpus Audit**: Full structural audit of 18 documents, page counts (696 total), character counts (2.06M), table density, amendment pairs (`Access-E-TRADE`), complexity tiers. Output `Data/corpus_manifest.json` and `Data/corpus_report.md`.
- [x] **Phase 2 — PDF Extraction Benchmark**: Head-to-head empirical benchmark between `PyMuPDF` and `pdfplumber`. PyMuPDF selected for 1.2x–2.3x speedup, native coordinate bounding boxes (`[x0, y0, x1, y1]`), and cleaner table boundary handling. Documented in `experiments/extraction/README.md` and `DECISIONS.md`.

---

## Master Phase Graph & Next Milestones
- [ ] **Phase 3 & 4 — Canonical Document Model & Structural Reconstruction**: Unified JSON schema for pages, blocks, sections, headings, tables with strict provenance and SEC noise tagging. (NEXT)
- [ ] **Phase 5 & 6 — Contract Intelligence & Hybrid Extraction**: Structured entity, term, and clause extraction (deterministic rules + LLM reasoning).
- [ ] **Phase 7, 8 & 9 — Obligation, Temporal & Event Engine**: Structured obligation objects, deterministic date/trigger calculators, contract lifecycle.
- [ ] **Phase 10, 11 & 12 — Chunking & Evaluation Dataset**: 40-question benchmark across 8 categories; section-aware vs. hierarchical chunking experiments.
- [ ] **Phase 13, 14, 15 & 16 — Retrieval Stack**: Embedding model evaluation, lexical BM25, hybrid RRF, and reranker benchmarking.
- [ ] **Phase 17, 18 & 19 — Evidence Layer & Grounded RAG with Verification**: Verifiable citation pipeline and answer verification engine.
- [ ] **Phase 20 — Contract Knowledge Graph Evaluation**: Empirically assess graph value for amendment and cross-contract dependency tracking.
- [ ] **Phase 21, 22, 23 & 24 — Agent Tool Layer, Router & Planner**: Typed tools, task router, multi-step planner, and session state.
- [ ] **Phase 25 & 26 — Version Intelligence & Change Impact Analysis**: Semantic section diffing, change classification, and impact mapping on obligations.
- [ ] **Phase 27 & 28 — Cross-Contract & Portfolio Intelligence**: Natural language portfolio queries and aggregate dashboards.
- [ ] **Phase 29 & 30 — Review Signals & "What Should I Worry About?" Agent**: Proactive risk flags and flagship operational review agent.
- [ ] **Phase 31 to 35 — Premium Frontend**: Operations dashboard, contract workspace, agent investigation panel, evidence drawer, timeline, and comparison UI.
- [ ] **Phase 36, 37 & 38 — Hardening, Security, Regression Suite & End-to-End Optimization**: Failure handling, controlled tools, full benchmark run.
- [ ] **Phase 39 & 40 — Demo & Submission Preparation**: 3-minute coherent demo script, README, presentation, and repository cleanup.

---

## Do Not Redo
- **Do NOT reconsider or re-evaluate problem statement**: PS4 is locked.
- **Do NOT re-gather or re-download the raw corpus**: 18 documents already exist in `Data/raw/`.
- **Do NOT modify or delete raw documents in `Data/raw/`**: The folder is strictly immutable.
- **Do NOT re-scan the entire repository for general context**: Use `docs/agent-context/` instead.
- **Do NOT build application components out of sequence**: Execute in bounded phases adhering to the stop-condition policy.
