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
- [x] **Phase 15 — Evidence Layer & Citation Integrity**: Implemented deterministic `EvidenceResolver`, `EvidenceValidator`, and structured `EvidenceBundle` in `src/evidence/`. Resolves chunks to canonical document/page/block/bbox with 100% citation validity across 1,321 references, 100% bbox validity, 100% unanswerable safety, and 1.12 ms average resolution latency. 12/12 targeted tests passed; 31/31 regression tests passed. Documented in `experiments/evidence/` and `docs/agent-context/DECISIONS.md`.
- [x] **Phase 16 — Grounded RAG & Verification Engine**: Implemented `GroundedAnswerGenerator`, `BaseLLMProvider`, and independent `ClaimVerifier` in `src/rag/`. Verifies extracted claims against `EvidenceBundle` spans for numeric, negation, and modality integrity. Full benchmark achieved 96.97% Grounded Answer Rate, 0.00% Unsupported Claim Rate, and 100.00% Unanswerable Safety Rate at 7.81 ms total latency. 11/11 targeted tests passed; 54/54 regression tests passed. Documented in `experiments/rag/` and `docs/agent-context/DECISIONS.md`.

---

## Master Phase Graph & Next Milestones
- [ ] **Phase 17 — Contract Knowledge Graph Evaluation**: Empirically assess graph value for amendment and cross-contract dependency tracking. (NEXT)
- [ ] **Phase 18 — Agent Tool Layer**: Deterministic typed tools and evidence-retrieval tool contracts.
- [ ] **Phase 19 — Agent Routing & Task Classification**: Rule-first task classifier and tool invocation router.
- [ ] **Phase 20 — Agent Planning & Session Orchestration**: Multi-step planner, execution loop, and memory state.
- [ ] **Phase 21 & 22 — Version Intelligence & Change Impact Analysis**: Semantic section diffing, change classification, and obligation impact mapping.
- [ ] **Phase 23 & 24 — Cross-Contract & Portfolio Intelligence**: Cross-document query synthesis and portfolio-level aggregation.
- [ ] **Phase 25 & 26 — Review Signals & "What Should I Worry About?" Agent**: Proactive risk signal detection and operational review agent.
- [ ] **Phase 27 to 31 — Premium Frontend Workspace**: Operations dashboard, contract viewer with PDF bounding-box evidence highlights, and audit drawer.
- [ ] **Phase 32 to 35 — Hardening, E2E Regression, Demo & Submission**: Failure recovery, end-to-end benchmark run, and demo script.

---

## Do Not Redo
- **Do NOT reconsider or re-evaluate problem statement**: PS4 is locked.
- **Do NOT re-gather or re-download the raw corpus**: 18 documents already exist in `Data/raw/`.
- **Do NOT modify or delete raw documents in `Data/raw/`**: The folder is strictly immutable.
- **Do NOT re-scan the entire repository for general context**: Use `docs/agent-context/` instead.
- **Do NOT build application components out of sequence**: Execute in bounded phases adhering to the stop-condition policy.
