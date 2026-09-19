# Evaluation Framework & Benchmark Methodology

Defines the quantitative evaluation criteria, regression standards, and benchmark suites for ContractLens.

---

## 1. Core Evaluation Dimensions

| Dimension | Metrics | Target Threshold | Validation Strategy |
| :--- | :--- | :--- | :--- |
| **Retrieval Quality** | Recall@3, Recall@5, Recall@10, MRR | Recall@5 >= 0.85, MRR >= 0.80 | 40-question golden query benchmark across contract corpus. |
| **Extraction Accuracy** | Field Precision/Recall (Parties, Dates, Terms) | Accuracy >= 90% | Exact match + normalized date/value checks against human ground truth. |
| **Obligation Extraction** | Actor, Action, Trigger, Deadline, Provenance | F1 >= 0.85 | Manual annotation cross-check on representative agreements. |
| **Citation & Grounding** | Citation Precision, Evidence Support, Hallucination Rate | 0% unsupported assertions | Citation verifier checks every claim against retrieved page/text coordinates. |
| **Agent Tool Execution** | Tool Selection Accuracy, Unnecessary Call Rate | Selection >= 90%, Zero redundant loops | Deterministic tool traces and regression test suite. |
| **System Latency** | End-to-End Answer Latency, Tool Overhead | Query < 3.5s, Complex compare < 8s | Wall-clock latency benchmarks on standard hardware. |

---

## 2. 40-Question Golden Evaluation Benchmark (Phase 10)

Implemented in `experiments/evaluation/benchmark_dataset.py` with schema in `benchmark_schema.py`:
- **8 Distinct Categories (5 questions each = 40 total)**:
  1. `CONTRACT_METADATA`: Effective dates, parties, term duration, governing laws, unanswerable expiration terms.
  2. `PARTIES_ENTITIES`: Precise entity names, corporate addresses, state of incorporation, unanswerable guarantor queries.
  3. `DATES_LIFECYCLE`: Commencement, initial terms, renewal notices, auto-renew windows, unanswerable retroactive dates.
  4. `PAYMENT_PRICING`: Net payment terms, late payment interest rates, invoicing frequency, fee adjustments, unanswerable pricing indexes.
  5. `TERMINATION_EXPIRATION`: Convenience termination, breach cure periods, insolvency termination, transition assistance, unanswerable penalty clauses.
  6. `OBLIGATIONS_COMPLIANCE`: Insurance coverage minimums, audit rights, data security/notification covenants, unanswerable ISO certifications.
  7. `CROSS_DOCUMENT_REASONING`: SOW vs. MSA precedence, DPA vs. Service Agreement data transfer priorities, multi-contract Net payment comparison (`Q32`), unanswerable multi-contract penalties.
  8. `VERSION_AMENDMENT_REASONING`: Modified terms in Access-E*TRADE amendment (term extension, storage fee deletion, cyber insurance addition, unchanged confidentiality, unanswerable arbitration revisions).

- **Structured Evidence & Provenance Requirements**:
  - Every question defines `target_documents`, `expected_pages`, `expected_sections`, `key_evidence_phrases`, `acceptable_variants`, and `reasoning_type`.
  - Exactly 7 questions are strictly `is_answerable=False` with explicit `unanswerable_reason` documentation to penalize hallucination.

---

## 3. Empirical Chunking Benchmark Results (Phase 11 & 12)

Evaluated across 9 corpus contracts (353 total pages) comparing **Fixed Sliding Window** (1000 chars, 200 overlap) against **Section-Aware Chunking** (hierarchical sections, subsections, exhibits, dedicated table units, max 2500 chars):

| Metric | Fixed Sliding Window | Section-Aware Chunker | Advantage |
| :--- | :--- | :--- | :--- |
| **Total Chunks Produced** | 1,606 chunks | 1,545 chunks | **-3.8% fewer chunks** (zero artificial overlap bloat) |
| **Mean Chunk Size** | 1,605.2 chars | 745.3 chars | Compact, atomic clause units |
| **Median Chunk Size** | 1,349.5 chars | 274.0 chars | Matches standard legal paragraph size |
| **Cross-Page Chunks** | 510 chunks (31.8%) | 252 chunks (16.3%) | **49.4% reduction in page fragmentation** |
| **Bounding Box Provenance** | 100.0% preserved | 100.0% preserved | Complete coordinate fidelity |
| **Benchmark Single-Chunk Containment** | 39 / 40 (97.5%) | 39 / 40 (97.5%) | Clean evidence localization |
| **Benchmark Multi-Chunk Required** | 1 / 40 (2.5%)* | 1 / 40 (2.5%)* | *Q32 is inherently a multi-contract comparison |
| **Evidence Severed / Missing** | 0 / 40 (0.0%) | 0 / 40 (0.0%) | Zero information loss |

### Boundary Observations & Empirical Learnings
1. **Clause Severance in Sliding Windows**: Sliding windows arbitrarily split legal clauses across numbers and definitions (e.g. splitting `Net` and `30` or separating cure notice periods from breach consequences).
2. **Table Integrity**: Sliding windows turn structured tables into fragmented ascii fragments. Section-aware chunking treats `TableData` as atomic `TABLE` chunks.
3. **Exhibit & Amendment Independence**: Section-aware chunking isolates schedules, exhibits, and amendment recitals, ensuring amendments and parents are not blended into single confusing text blocks.

---

## 4. Regression Prevention Rule
Before accepting any algorithmic change (chunking, embeddings, hybrid RRF weights, prompt engineering, reranker):
1. Run evaluation against golden benchmark.
2. If new approach improves one metric (e.g., recall) but impairs another (e.g., latency, grounding, precision), require explicit tradeoff justification in `DECISIONS.md`.
3. Reject changes that introduce hallucinations or broken citations.
