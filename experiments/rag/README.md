# Empirical Grounded RAG & Verification Report (Phase 16)

Evaluates the Grounded RAG & Claim Verification Engine across all 40 questions of the ContractLens golden benchmark.

---

## 1. Primary Grounding & Verification Metrics

| Metric | Phase 16 Result | Definition |
| :--- | :---: | :--- |
| **Grounded Answer Rate** | **96.97%** | Percentage of answerable questions producing fully supported, cited answers |
| **Claim Support Rate** | **96.97%** | Percentage of extracted factual claims classified as `SUPPORTED` |
| **Unsupported Claim Rate** | **0.00%** | Claims rejected due to lack of evidence alignment |
| **Contradiction Rate** | **0.00%** | Claims identified as contradicting contract evidence (e.g. negation mismatch) |
| **Citation Precision** | **96.97%** | Attached citations pointing to verified EvidenceBundle coordinates |
| **Citation Completeness** | **96.97%** | Claims backed by at least one valid supporting citation |
| **Unanswerable Safety Rate** | **100.00%** | 100% safe handling with zero fabricated claims or hallucinated citations |

---

## 2. Granular Latency Breakdown

| Stage | Avg Latency | Component |
| :--- | :---: | :--- |
| **Retrieval** | **5.85 ms** | Hybrid RRF candidate search ($k=60$) |
| **Evidence Layer** | **1.03 ms** | Block-level resolution & bbox validation (Phase 15) |
| **Generation** | **0.73 ms** | Structured claim generation |
| **Verification** | **0.13 ms** | Deterministic factual, negation, and numeric claim audit |
| **Total Pipeline** | **7.81 ms** | Complete end-to-end response time |

---

## 3. Grounding Principles & Safety Invariants
1. **EvidenceBundle as Boundary**: The LLM synthesizes answers strictly from supplied `[E1]`, `[E2]` evidence blocks. Outside world knowledge is explicitly forbidden.
2. **Independent Verifier**: Claims proposed by the LLM are independently audited by `ClaimVerifier`; model-claimed verification statuses are never trusted without proof.
3. **Deterministic Citations**: Citations are derived directly from verified canonical blocks in `EvidenceBundle`, guaranteeing that no model can invent fake pages, blocks, or filenames.
