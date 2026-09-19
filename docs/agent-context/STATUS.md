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
- [x] **Phase 3 & 4 — Canonical Document Model & Structural Reconstruction**: Provenance-first Pydantic schemas (`src/models/canonical.py`) and deterministic reconstructor (`src/ingestion/reconstructor.py`). Preserves bounding boxes, reading order, table matrices, signatures, exhibit markers, and non-destructive SEC noise tags. 100% test pass (`tests/test_canonical_reconstruction.py`).
- [x] **Phase 5 & 6 — Contract Intelligence & Hybrid Extraction**: Strongly-typed intelligence models (`src/models/intelligence.py`) and hybrid extractor (`src/ingestion/extractor.py`). Extracts parties, dates, Net payment terms, governing laws, termination notice periods, and amendment modifications with mandatory clause provenance. 100% test pass (`tests/test_intelligence_extraction.py`).
- [x] **Phase 7, 8 & 9 — Obligation, Temporal & Event Engine**: Strongly-typed `ContractObligation` model, deterministic `TemporalEngine` with 7 temporal types, recurrence rules, non-fabricating date calculator, and `LifecycleEventEngine`. 100% test pass (`tests/test_obligation_temporal.py`). Benchmark documented in `experiments/obligations/`.
- [x] **Phase 10, 11 & 12 — Evaluation Dataset & Contract-Aware Chunking Experiments**: Created reproducible 40-question benchmark with 7 unanswerable questions, acceptable variants, and exact physical provenance. Implemented `FixedSlidingWindowChunker` and `SectionAwareChunker` preserving 100% bounding box provenance. Demonstrated 49.4% reduction in cross-page fragmentation and 97.5% single-chunk containment. Documented in `experiments/chunking/` and `docs/agent-context/EVALUATION.md`.
- [x] **Phase 13 — Empirical Retrieval Benchmark (Lexical, Dense, Hybrid RRF)**: Evaluated BM25, Dense Semantic LSA, and Hybrid RRF against all 40 questions of the golden benchmark across 1,545 chunks. Hybrid RRF established clear superiority with 87.88% Recall@5, 93.94% Recall@10, 87.88% evidence containment, and 14.79 ms average latency. Documented in `experiments/retrieval/` and `docs/agent-context/DECISIONS.md`.
- [x] **Phase 14 — Empirical Reranking Experiments (Justify vs. Defer)**: Benchmarked FlashRank TinyBERT ONNX cross-encoder against BM25 and Hybrid RRF Top-10 pools across 1,545 chunks. Empirical results showed precision boost (Hybrid MRR: 0.6646 -> 0.7631, R@1: 51.52% -> 66.67%) but multiplied latency by ~4x to 15x (7ms -> 29ms+). Decision: defer mandatory reranker from default single-turn RAG loop, retain Hybrid RRF as baseline, preserve FlashRank as optional precision tier. Documented in `experiments/reranking/` and `docs/agent-context/DECISIONS.md`.

---

## Master Phase Graph & Next Milestones
- [ ] **Phase 15 & 16 — Retrieval Optimization & Index Packaging**: Finalize unified retrieval service and provenance packaging. (NEXT)
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
