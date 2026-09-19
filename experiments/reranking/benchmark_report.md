# Empirical Reranking Benchmark Report (Phase 14)

Evaluates whether cross-encoder reranking (FlashRank `ms-marco-TinyBERT-L-2-v2`, ~3.3MB) improves ordering within the Top-10 retrieved candidate pool for BM25 and Hybrid RRF across the 40-question golden contract benchmark.

---

## 1. Primary Pipeline Comparison Matrix

| Pipeline | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR | Evidence Containment | Provenance Correctness | Avg Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BM25_Baseline** | 0.6061 | 0.8485 | 0.8485 | 0.9091 | 0.7294 | 0.8788 | 0.8182 | 2.13 ms |
| **BM25_FlashRank** | 0.6667 | 0.8485 | 0.8485 | 0.9091 | 0.7563 | 0.8788 | 0.8182 | 23.67 ms |
| **Hybrid_RRF_Baseline** | 0.5152 | 0.7576 | 0.8788 | 0.9394 | 0.6646 | 0.8788 | 0.8485 | 7.26 ms |
| **Hybrid_FlashRank** | 0.6667 | 0.8485 | 0.8788 | 0.9394 | 0.7631 | 0.8788 | 0.8788 | 29.06 ms |

*Note: Evaluated on answerable benchmark questions (N=33). All 7 unanswerable questions evaluated separately with 100% safe non-hallucination handling.*

---

## 2. Category-Level Performance Breakdown (Recall@3 & MRR)

| Category (Count) | BM25 R@3 (MRR) | BM25+Rerank R@3 (MRR) | Hybrid R@3 (MRR) | Hybrid+Rerank R@3 (MRR) |
| :--- | :---: | :---: | :---: | :---: |
| **`amendments_versions`** (4) | 1.00 (0.88) | 1.00 (0.71) | 1.00 (0.58) | 1.00 (0.75) |
| **`cross_document`** (4) | 0.75 (0.53) | 0.75 (0.54) | 0.50 (0.45) | 0.75 (0.48) |
| **`dates_lifecycle`** (4) | 0.75 (0.75) | 0.75 (0.75) | 0.75 (0.75) | 0.75 (0.75) |
| **`metadata`** (4) | 0.50 (0.36) | 0.50 (0.36) | 0.50 (0.40) | 0.50 (0.38) |
| **`obligations`** (5) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.90) | 1.00 (1.00) |
| **`parties`** (4) | 1.00 (0.62) | 1.00 (0.88) | 0.75 (0.80) | 1.00 (0.88) |
| **`payment`** (4) | 0.75 (0.75) | 0.75 (0.75) | 0.50 (0.50) | 0.75 (0.81) |
| **`termination`** (4) | 1.00 (0.88) | 1.00 (1.00) | 1.00 (0.88) | 1.00 (1.00) |

---

## 3. Engineering Analysis: Justify or Defer Reranker?
1. **Recall & MRR Impact**:
   - Compare top-1 precision (`Recall@1`) and `MRR` before and after reranking.
   - Inspect whether the cross-encoder correctly promotes relevant legal clauses or suffers from domain transfer penalty on boilerplate legal language.
2. **Latency Trade-Off**:
   - BM25 candidate generation operates at ~3 ms.
   - Cross-encoder reranking over 10 candidates adds inference overhead.
   - Does the marginal precision gain justify the latency overhead?
