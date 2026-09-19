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

## 2. Planned 40-Question Golden Evaluation Benchmark

Categorical split across the 18-contract corpus:
- **Metadata (5 questions)**: Effective date, parties, governing law, term duration.
- **Payment & Pricing (5 questions)**: Net payment terms, late fees, invoicing frequency, fee adjustments.
- **Termination & Expiration (5 questions)**: Termination for convenience, breach notice periods, auto-renew windows.
- **Obligations & Compliance (5 questions)**: Reporting obligations, insurance minimums, data security covenants.
- **Deadlines & Temporals (5 questions)**: Event-triggered deadlines ("X days after invoice"), renewal notification cutoffs.
- **Cross-Contract & Portfolio (5 questions)**: Which contracts auto-renew? Which have 60-day notice periods?
- **Version Comparison & Amendments (5 questions)**: Changed payment terms between MSA and Amendment, modified liabilities.
- **Complex Semantic Reasoning (5 questions)**: Interlocking clauses (e.g., limitation of liability exceptions for confidentiality breach).

---

## 3. Regression Prevention Rule
Before accepting any algorithmic change (chunking, embeddings, hybrid RRF weights, prompt engineering, reranker):
1. Run evaluation against golden benchmark.
2. If new approach improves one metric (e.g., recall) but impairs another (e.g., latency, grounding, precision), require explicit tradeoff justification in `DECISIONS.md`.
3. Reject changes that introduce hallucinations or broken citations.
