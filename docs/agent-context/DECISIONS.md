# Architecture & Engineering Decisions

Log of accepted decisions and intentionally undecided choices. Update this document as architectural directions are finalized.

---

## Accepted Decisions

### Decision: Problem Statement Selection
- **Status**: LOCKED
- **Selection**: PS4 — ContractLens: Business Contract Review & Obligation Tracking Agent.
- **Context**: Hackathon 2026 selected scope.

### Decision: Raw Contract Corpus Sourcing
- **Status**: Accepted
- **Selection**: 18 real-world, publicly available commercial contract and amendment PDFs placed in `Data/raw/`.
- **Context**: Real-world documents ensure rigorous testing of real-world layout, boilerplate clauses, amendments, and definitions.

### Decision: Raw Data Immutability
- **Status**: Accepted
- **Selection**: Files inside `Data/raw/` are strictly read-only and immutable.
- **Context**: Ensures evaluation consistency and prevents corrupting original source material.

### Decision: Context & Agent Memory Architecture
- **Status**: Accepted
- **Selection**: 3-layer hierarchy (Always-on Rules in `.agents/rules/`, Compact Project Memory in `docs/agent-context/`, Task Skills in `.agents/skills/`).
- **Context**: Minimizes repetitive repository audits and token spend across agent turns.

### Decision: PDF Parsing Engine
- **Status**: Accepted
- **Selection**: PyMuPDF (`fitz`).
- **Rationale**: Validated via Phase 2 benchmark against `pdfplumber` across short, medium, and 176-page stress test documents. PyMuPDF delivered 1.2x to 2.3x lower extraction latency, native geometric bounding boxes (`[x0, y0, x1, y1]`), clean table boundary detection without over-segmenting horizontal rules, and 100% digital vector character capture across all 696 corpus pages.

### Decision: Canonical Document Model & Structural Reconstruction
- **Status**: Accepted
- **Selection**: Pydantic-based `CanonicalDocument` schema with `CanonicalPage`, `CanonicalBlock`, `CanonicalSection`, and `TableData`.
- **Rationale**: Validated via Phase 3 & 4 benchmarks across representative contracts. The model preserves exact physical page numbers, geometric bounding boxes, reading order, table matrices, and clause hierarchies. Crucially, SEC filing noise (headers/URLs) is tagged (`is_sec_noise=True`) rather than destructively deleted, guaranteeing that original raw text remains 100% recoverable.

### Decision: Contract Intelligence & Hybrid Extraction
- **Status**: Accepted
- **Selection**: Deterministic pattern extraction with typed normalization, mandatory `EvidenceReference` provenance, and explicit `is_found=False` for missing/redacted fields.
- **Rationale**: Validated via Phase 5 & 6 benchmark on core agreements. Deterministic extraction reliably captures parties, effective dates, Net payment terms (Net 30, Net 60), termination notice days (30, 60), and amendment modifications (`DELETE_AND_REPLACE`, `ADD_COVERAGE`) without LLM cost or latency. Missing or redacted fields (`[*****]`) return explicit null states rather than hallucinations.

### Decision: Obligation, Temporal & Lifecycle Engine
- **Status**: Accepted
- **Selection**: Strongly-typed `ContractObligation`, `TemporalConstraint`, and `LifecycleEvent` representations.
- **Rationale**: Validated via Phase 7–9 benchmark across 779 obligations. Distinguishes 7 temporal categories (`FIXED_DATE`, `RELATIVE_OFFSET`, `EVENT_RELATIVE`, `RECURRING`, `CONDITIONAL`, `ONGOING`, `UNSPECIFIED`). Decouples relative offsets (e.g., Net 30, 10 days post-breach) from calendar dates; unknown anchors remain explicitly `unresolved` rather than fabricated. Recurrence is captured via rules (`RecurrenceRule`) without premature infinite materialization. Real-world completion status remains strictly `UNKNOWN` in the absence of external ERP data.

### Decision: Contract-Aware Chunking Strategy
- **Status**: Accepted
- **Selection**: `SectionAwareChunker` (hierarchical section, subsection, paragraph groups, exhibits, and dedicated table chunks).
- **Rationale**: Validated via Phase 11 & 12 benchmark across 353 corpus pages and the 40-question golden evaluation suite. Section-aware chunking generated 1,545 atomic chunks (vs. 1,606 for sliding windows), cut cross-page clause splits by 49.4% (from 31.8% down to 16.3%), preserved complete tabular matrices as distinct units, and contained 97.5% of benchmark evidence within single chunk boundaries with 100% coordinate bounding box fidelity.

### Decision: Empirical Retrieval Architecture (BM25 + Dense Semantic via Hybrid RRF)
- **Status**: Accepted
- **Selection**: Hybrid Reciprocal Rank Fusion (`HybridRRFRetriever`, `k=60`) combining BM25 Lexical scoring with Dense Semantic LSA vector representations.
- **Rationale**: Validated via Phase 13 benchmark across all 40 questions of the golden benchmark (N=33 answerable, N=7 unanswerable):
  - **Recall@5**: Hybrid RRF achieved **87.88%** (vs. 84.85% for BM25 and 78.79% for Dense LSA alone).
  - **Recall@10**: Hybrid RRF achieved **93.94%** (vs. 90.91% for BM25 and 87.88% for Dense LSA).
  - **Evidence Containment**: **87.88%** of answerable benchmark questions retrieved full gold evidence within the top ranks.
  - **Provenance Correctness**: **84.85%** of retrieved evidence matched exact ground-truth physical page coordinates.
  - **Latency**: Highly efficient average latency of **14.79 ms** per query without external network dependencies.
  - **Amendment Differentiation**: Successfully isolates amendment clauses at Rank 1 in the Access-E*TRADE parent/child benchmark.
  - **Unanswerable Query Safety**: 100% safe handling with zero hallucinated false claims.
### Decision: Empirical Reranking Evaluation (Justify vs. Defer Architecture)
- **Status**: Accepted
- **Selection**: Defer mandatory cross-encoder reranking from the default retrieval loop; retain Hybrid RRF ($k=60$) as the primary retrieval baseline; preserve `FlashRankReranker` (`ms-marco-TinyBERT-L-2-v2`) as an optional precision-tier pass for high-ambiguity or deep-audit queries.
- **Rationale**: Validated via Phase 14 empirical evaluation across 1,545 chunks on the 40-question golden benchmark:
  - **Marginal Precision Gain**: On Hybrid RRF, FlashRank improves `Recall@1` from **51.52% to 66.67%** (+15.15%) and `MRR` from **0.6646 to 0.7631** (+0.0985). `Recall@3` reaches **84.85%** (matching un-reranked BM25), while `Recall@5` (**87.88%**) and `Recall@10` (**93.94%**) remain identical because reranking re-orders rather than expands candidates.
  - **Latency Trade-Off**: Baseline Hybrid RRF executes in **7.26 ms** (and BM25 in **2.13 ms**). Adding cross-encoder inference over 10 candidates increases query latency to **29.06 ms** (a ~4x increase) and up to **500 ms** under full cold-cache CPU inference.
  - **Boilerplate Legal Language Penalty**: The evaluated MS-MARCO FlashRank reranker showed domain-specific ranking failures on amendment evidence in the ContractLens benchmark, slightly penalizing amendment-specific modifications where parent agreements and amendments share identical clause titles (`Q36` dropped from Rank 1 to Rank 2, `Q37` dropped from Rank 2 to Rank 3).
  - **Defensible Conclusion**: In a latency-sensitive legal RAG system targeting sub-50ms tool execution, Hybrid RRF provides 93.94% Recall@10 and 87.88% containment at 7 ms. Forcing a mandatory reranker multiplies latency for minor top-1 gains. Therefore, the reranker is **deferred** from default single-turn retrieval and retained as a configurable module.

### Decision: Deterministic Evidence Layer & Citation Integrity
- **Status**: Accepted
- **Selection**: Deterministic `EvidenceResolver` and `EvidenceValidator` producing strongly-typed `EvidenceBundle` instances containing deduplicated `EvidenceSpan` and `EvidenceCitation` records.
- **Rationale**: Validated via Phase 15 empirical benchmark across 1,321 evaluated citations on the 40-question golden dataset:
  - **Resolution & Citation Validity**: Achieved **100.00%** citation validity rate across all 1,321 canonical block references. Every citation resolves back to physical PDF pages and native geometric bounding boxes ($x_0, y_0, x_1, y_1$).
  - **Zero Fabrication**: Bounding-box validity and provenance consistency reached **100.00%**. Unanswerable query safety reached **100.00%** with zero fabricated citations or hallucinated spans.
  - **Document & Page Accuracy**: Document accuracy reached **100.00%** and page-level retrieval accuracy reached **87.88%** on answerable queries with **81.82%** full evidence containment in top-5 chunks.
  - **Sub-Millisecond Resolution Latency**: Evidence resolution requires on average **1.12 ms** (combined with Hybrid RRF at 6.10 ms for **7.23 ms** total pipeline latency), well within the sub-50ms real-time agent budget.
  - **Architecture Role**: Establishes a deterministic contract boundary between Retrieval and Grounded RAG. Evidence is resolved through authoritative document/block provenance rather than generated by the language model.

### Decision: Grounded RAG & Independent Claim Verification Engine
- **Status**: Accepted
- **Selection**: Decoupled `GroundedAnswerGenerator` and deterministic `ClaimVerifier` operating over structured `GroundedClaim` assertions and verified `EvidenceBundle` spans.
- **Rationale**: Validated via Phase 16 empirical benchmark across all 40 golden benchmark questions and 33 factual assertions:
  - **The Grounding Boundary**: The `EvidenceBundle` acts as the strict authoritative boundary. Outside world knowledge is forbidden in prompts; LLMs only synthesize answers from numbered `[E1]`, `[E2]` evidence blocks.
  - **Independent Claim Audit**: Claims proposed by the LLM are never trusted at face value. `ClaimVerifier` deterministically checks numeric alignment (e.g. Net 30 vs Net 60), negation/contradiction (e.g. "without automatic renewal"), and modality mismatches ('may' vs 'shall').
  - **Benchmark Results**: Achieved **96.97%** Grounded Answer Rate, **96.97%** Claim Support Rate, **0.00%** Unsupported Claim Rate, **0.00%** Contradiction Rate, and **100.00%** Unanswerable Safety Rate on strictly unanswerable queries (safely emitting controlled insufficient-evidence states with zero fabricated citations).
  - **Latency Profile**: Average total pipeline latency is **7.81 ms** (Retrieval: 5.85 ms, Evidence Resolution: 1.03 ms, Structured Claim Generation: 0.73 ms, Deterministic Verification: 0.13 ms).

### Decision: Provenance-Aware Contract Knowledge Graph & Cross-Contract Reasoning
- **Status**: Accepted
- **Selection**: In-memory, typed, provenance-aware Knowledge Graph (`KnowledgeGraph`, `GraphNode`, `GraphEdge`, `GraphFact`) with multi-attribute inverted index (`GraphIndex`) and deterministic cross-contract query engine (`ContractGraphQueryEngine`).
- **Rationale**: Validated via Phase 17 empirical benchmark across all 18 contracts (696 pages) in the ContractLens corpus:
  - **In-Memory & Lightweight**: No external graph database (e.g. Neo4j) required. Graph construction takes **488.28 ms** for 3,287 nodes and 4,359 edges; validation executes in **22.88 ms**; query latency averages **0.037 ms** across complex relationship traversals.
  - **100% Provenance Coverage**: Every `GraphFact` and entity preserves an authoritative `EvidenceReference` pointing to physical page numbers, canonical block IDs, and native bounding box coordinates. Zero facts exist without provenance.
  - **Zero Unsupported Fact & Zero Orphan Invariants**: Validation enforces 0.0% orphan edges and 0.0% invalid bounding box geometries.
  - **Preservation of Precedence & Conflicts**: Base contracts and amendments exist as distinct nodes linked by `AMENDS` and `HAS_AMENDMENT` edges. Amendment facts do not destructively overwrite parent terms, enabling queries to audit both original and modified conditions.
  - **Unknown != Negative**: Unknown or redacted attributes remain explicitly unasserted or marked `unresolved` rather than guessed or fabricated.
  - **Cross-Contract Reasoning Benchmark**: Achieved **100.0%** accuracy (10/10 test queries passed) across direct entity lookups, party relationship graphs, cross-contract party networks, payment term filtering, renewal provisions, termination notice periods, and safe rejection of non-existent entities.

### Decision: Controlled Contract Agent Tool Layer & Rule-First Orchestration
- **Status**: Accepted
- **Selection**: Controlled orchestrator (`ContractAgent`) operating over a typed tool registry (`ToolRegistry`), deterministic router (`AgentRouter`), planner (`DeterministicPlanner`), and bounded executor (`AgentExecutor`).
- **Rationale**: Validated via Phase 18 empirical benchmark across 16 representative queries spanning all 8 routing categories:
  - **Agent as Orchestrator, Not Source of Truth**: The agent decides *when* to invoke tools (graph, retrieval, details, obligations, timeline, amendments); it never invents contractual facts. The hierarchy of trust remains: Canonical contract evidence > EvidenceBundle > Verified structured facts > Knowledge Graph > Agent reasoning > Verified Answer.
  - **Deterministic Rule-First Routing**: 100.0% Tool Selection Accuracy across direct graph queries, retrieval, contract details, obligations, lifecycle timelines, amendments, and unanswerable questions without LLM latency or hallucination risk.
  - **Strict Provenance Preservation**: All structured tool outputs retain their native `EvidenceReference` and coordinate bounding boxes. Facts and commitments are converted to `EvidenceSpans` ensuring downstream Grounded RAG has direct access to provenance.
  - **Mandatory Phase 16 Verification Bridge**: Final answers are synthesized exclusively through `build_grounded_answer` (Phase 16 Grounded RAG + `ClaimVerifier`). No unverified natural-language text is returned.
  - **Zero Unsupported Claims & 100% Unanswerable Safety**: 0.0% unsupported claims reached final answers; 100.0% unanswerable safety rate achieved with controlled insufficient-evidence states and zero fabricated citations.
  - **Hard Execution Bounds**: Enforces `MAX_STEPS = 6`, `MAX_TOOL_CALLS = 6`, `MAX_RETRIES = 1` preventing runaway loops.
  - **Auditable AgentTrace Without Hidden CoT**: The agent trace records explicit tool names, inputs, outputs, status, and latency without exposing or storing private chain-of-thought tokens.
  - **Sub-5ms Execution Latency**: Average end-to-end execution latency across deterministic tools and local grounded synthesis is **1.72 ms** per query.

### Decision: Semantic Query Understanding Layer & Canonical Entity Ontology
- **Status**: Accepted (Phase 19)
- **Selection**: Deterministic `ContractQueryUnderstander` and `ContractRoleOntology` executing in front of `AgentRouter`.
- **Rationale**:
  - **Typed Structural Understanding**: Replaces ad-hoc string regexes in `AgentRouter` with strongly typed models: `QueryIntent`, `CanonicalRole`, `RoleCandidate`, `EntityReference`, `TemporalCue`, `ComparisonCue`, `ExpandedQuery`, and `QueryUnderstanding`.
  - **Contract-Evidence Role Resolution**: Common conversational roles (`vendor`, `supplier`, `customer`, `buyer`, etc.) map to a minimal canonical ontology (`SUPPLIER`, `CUSTOMER`, `SERVICE_PROVIDER`, `BUYER`, `LICENSOR`, `LICENSEE`, `BORROWER`, `LENDER`). Roles are candidates, not blind party identities; resolution resolves against verified contract party evidence. If multiple counterparties match, status is flagged as `AMBIGUOUS`. Unsubstantiated or unknown roles remain `UNRESOLVED` or `UNKNOWN`.
  - **Zero Date Fabrication**: Conversational temporal expressions (`within 30 days`, `after termination`) are parsed into structured offsets and anchor event types. If the anchor date is unknown or ungrounded, `anchor_status` remains `UNRESOLVED` with `computed_target_date=None`.
  - **Controlled Query Expansion & Exact Query Preservation**: The original user query is strictly preserved. Expansion terms and resolved counterparties are appended only through `ExpandedQuery` with non-fabricating domain synonyms and contract-grounded metadata.
  - **100% Final Answer Grounding**: Solves conversational counterparty obligation queries (such as AMX vendor queries) cleanly, achieving 100.0% Final Answer Grounding, 100.0% Tool Execution, 100.0% Citation Validity, 0.0% Unsupported Claims, and 100.0% Unanswerable Safety on the benchmark.
  - **Ontology Granularity & Adversarial Hardening (Phase 22 Backlog)**: Current mapping groups common terms (e.g., `buyer` -> `CUSTOMER`, `manufacturer` -> `SUPPLIER`). While safe and deterministic for current contracts, contracts may differentiate `supplier ≠ manufacturer`, `vendor ≠ service provider`, or `buyer ≠ customer`. This distinction is recorded for testing in the Phase 22 adversarial evaluation suite rather than prematurely complicating the Phase 19 ontology.

### Decision: Empirical Evaluation of Query-Adaptive Retrieval & Baseline Retention
- **Status**: Evaluated & Retained Hybrid RRF Baseline as Default (Phase 20)
- **Selection**: Implemented `AdaptiveRetriever` supporting intent-aware candidate generation, query expansion, difficulty detection, and FlashRank reranking (`src/retrieval/adaptive.py`). Empirical evaluation across the 40-question benchmark showed:
  - **Baseline Retained**: `Hybrid_RRF_Baseline` achieved the highest top-5 recall (**87.88%** R@5, **93.94%** R@10, **87.88%** Evidence Containment) at **12.27 ms** average latency.
  - **Expansion Tradeoff**: Unconditional semantic query expansion broadened candidate pools on legal terminology, reducing R@5 to 78.79%.
  - **Cross-Encoder Precision vs Latency**: FlashRank cross-encoder boosts Top-1 precision (R@1: 51.52% -> 66.67%, MRR: 0.6646 -> 0.7508) but introduces a 3x-5x latency overhead (40-60 ms).
  - **Architecture Decision**: Retain `HybridRRFRetriever` as the primary production retrieval engine for fast single-turn RAG, while providing `AdaptiveRetriever` with selective FlashRank reranking as an opt-in precision configuration for complex, multi-candidate queries. 100% citation validity, 0% unsupported claims, and 100% unanswerable safety preserved across all configurations.

---

## Intentionally Undecided Decisions (Pending Future Milestones)

- **Backend Language / Framework**: Undecided (e.g., Python FastAPI / Flask / Node.js).
- **Vector Database / Dedicated Vector Store**: Intentionally deferred until scale warrants.
- **Frontend Framework**: Undecided (e.g., React + Vite, Next.js, Streamlit).
- **Database for Structured Metadata**: Undecided (e.g., SQLite, PostgreSQL).

