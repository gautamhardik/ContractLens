# Empirical Evidence Layer & Citation Integrity Report (Phase 15)

Evaluates the deterministic Evidence Layer bridging Hybrid RRF Retrieval and downstream Grounded RAG (Phase 16) across the 40-question golden contract benchmark.

---

## 1. Summary Metrics

| Metric | Phase 15 Result | Definition / Scope |
| :--- | :---: | :--- |
| **Questions Evaluated** | **40** | 33 Answerable, 7 Strictly Unanswerable |
| **Total Citations Evaluated** | **1321** | All canonical block references across Top-5 retrieved chunks |
| **Citation Validity Rate** | **100.00%** | Verified against canonical document, page, and block store |
| **Document Accuracy** | **100.00%** | Correct target document identified in resolved evidence spans |
| **Page Accuracy** | **87.88%** | Exact target page resolved in canonical evidence spans |
| **Evidence Containment** | **81.82%** | Complete ground-truth evidence keyphrases present in spans |
| **Bounding-Box Validity** | **100.00%** | Valid coordinates satisfying $x_0 \le x_1, y_0 \le y_1$ within page geometry |
| **Provenance Consistency** | **100.00%** | Block, page, and document chain 100% verified with zero mismatch |
| **Unanswerable Safety** | **100.00%** | Zero hallucinated citations or fabricated evidence on unanswerable queries |

---

## 2. Latency Breakdown

| Pipeline Stage | Average Latency | Architectural Role |
| :--- | :---: | :--- |
| **Hybrid RRF Retrieval** | **6.10 ms** | BM25 + Dense LSA candidate generation ($k=60$) |
| **Evidence Resolution** | **1.12 ms** | Canonical block resolution, deduplication & bbox check |
| **Total End-to-End Pipeline** | **7.23 ms** | Sub-50ms execution meeting strict real-time agent budget |

---

## 3. Evidence Deduplication & Ordering Guarantees
- **Deduplication**: When overlapping sliding windows or adjacent section chunks reference the same canonical block, the block is merged into a single `EvidenceSpan`, aggregating all source chunk IDs into `metadata["source_chunk_ids"]`.
- **Deterministic Ordering**: Output `EvidenceBundle` instances sort evidence strictly by `(document_id, page_number, reading_order, block_id)`.
- **Zero LLM Dependency**: Operates 100% deterministically on canonical structures with zero generative model calls.
