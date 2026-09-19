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
- [x] **Phase 17 — Contract Knowledge Graph & Cross-Contract Reasoning**: Implemented in-memory, typed, provenance-aware Knowledge Graph (`KnowledgeGraph`, `GraphNode`, `GraphEdge`, `GraphFact`), multi-attribute inverted index (`GraphIndex`), validator (`GraphValidator`), and deterministic query engine (`ContractGraphQueryEngine`) in `src/graph/`. Built across complete 18-contract corpus (696 pages), indexing 3,287 nodes, 4,359 edges, and 61 contractual facts with 100.0% provenance coverage, 0.0% orphan edges, and 0.0% invalid bounding boxes. Evaluated 10 structured cross-contract benchmark queries achieving 100.0% reasoning accuracy at 0.037 ms average query latency. 18/18 targeted tests passed; 78/78 regression tests passed. Documented in `experiments/graph/` and `docs/agent-context/DECISIONS.md`.
- [x] **Phase 18 — Controlled Contract Agent Tool Layer**: Implemented typed `AgentTool` protocol, `ToolRegistry`, core tools (`search_contract_evidence`, `query_contract_graph`, `get_contract_details`, `get_contract_obligations`, `get_contract_timeline`, `get_contract_amendments`, `build_grounded_answer`), deterministic router (`AgentRouter`), planner (`DeterministicPlanner`), bounded executor (`AgentExecutor`), and `ContractAgent` facade in `src/agent/`. Benchmark over 16 queries across 8 categories achieved 100.0% tool selection accuracy, 96.8% execution success, 92.3% final answer grounding, 100.0% citation validity, 0.0% unsupported claims, and 100.0% unanswerable safety at 1.72 ms average latency. 19/19 targeted tests passed; 97/97 full regression tests passed. Documented in `experiments/agent/` and `docs/agent-context/DECISIONS.md`.
- [x] **Phase 18.1 — Conversational Role-Alias Resolution Hardening**: Hardened `AgentRouter` and `GetContractObligationsTool` with canonical role-synonym resolution and contract-scoped entity mapping. Resolves conversational queries (`"vendor"`, `"supplier"`, `"customer"`) to counterparty obligations without false assumptions, boosting Final Answer Grounding from 92.31% to **100.0%** (13/13 answerable queries grounded) with 100.0% tool execution success, 0.0% unsupported claims, and 100.0% unanswerable safety. 7/7 targeted role-resolution tests passed; 26/26 agent test suite passed. Documented in `experiments/agent/README.md`.
- [x] **Phase 19 — Contract Query Understanding & Canonical Entity Ontology**: Built a deterministic, contract-aware semantic query understanding layer (`src/agent/understanding.py`) positioned in front of `AgentRouter`. Implemented strongly typed models (`QueryIntent`, `CanonicalRole`, `RoleCandidate`, `EntityReference`, `TemporalCue`, `ComparisonCue`, `ExpandedQuery`, `QueryUnderstanding`), canonical role ontology (`SUPPLIER`, `CUSTOMER`, `SERVICE_PROVIDER`, `BUYER`, `LICENSOR`, `LICENSEE`, `BORROWER`, `LENDER`), deterministic contract-scoped party-role resolution, unanchored temporal cue extraction without date fabrication, and controlled query expansion while strictly preserving the original user query. 41/41 agent suite tests passed; 119/119 full regression tests passed. Phase 18 benchmark maintains 100.0% Final Answer Grounding, 100.0% Tool Execution, 100.0% Citation Validity, 0.0% Unsupported Claims, and 100.0% Unanswerable Safety.
- [x] **Phase 20 — Query-Adaptive Retrieval & Selective Reranking Benchmark**: Implemented `RetrievalQuery` consuming Phase 19 `QueryUnderstanding`, intent-aware candidate weighting, `DifficultyDetector`, and `AdaptiveRetriever` with selective FlashRank cross-encoder reranking (`src/retrieval/adaptive.py`). Evaluated 5 strategies across the 40-question benchmark: `Hybrid_RRF_Baseline` established superior top-5 recall (87.88% R@5, 93.94% R@10, 87.88% containment at 12.27 ms), while FlashRank delivered higher R@1 (66.67% vs 51.52%) at a 3x-5x latency cost (40-60 ms). Retained `HybridRRFRetriever` as default production retriever with `AdaptiveRetriever` as an opt-in precision tier. 11/11 targeted tests passed; 41/41 agent suite tests passed; 130/130 full regression tests passed. Documented in `experiments/retrieval/README.md` and `docs/agent-context/DECISIONS.md`.

---

## Master Phase Graph & Next Milestones
- [ ] **Phase 21 — Structured Amendment & Version Intelligence**: Parent/amendment resolution, section alignment, before/after structured change modeling, full-force clause handling, and grounded impact synthesis. (NEXT)
- [ ] **Phase 22 — Hard Adversarial Benchmark & Core Backend Freeze**: 60-80 adversarial stress queries attacking role collisions, unanchored dates, and unsupported facts before freezing the core engine.
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
