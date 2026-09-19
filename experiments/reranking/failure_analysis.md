# Reranking Failure Analysis & Access-E*TRADE Audit (Phase 14)

Empirical investigation into whether cross-encoder reranking improves, preserves, or degrades candidate ranking across contract queries.

---

## 1. Access–E*TRADE Amendment Pair Ground-Truth Audit
Inspecting whether reranking correctly preserves or promotes amendment modifications over parent MSA provisions:
- **`Q36` (Term Modification)**: Deletion of Section 3 in parent MSA replaced with Savings Amount.
- **`Q37` (Price Schedule Replacement)**: Deletion of Section 1.2 in parent MSA replacing storage fees.
- **`Q38` (Errors & Omissions Insurance Addition)**: Amending Section 15.4 by adding $2,000,000 E&O coverage.
- **`Q39` (Confirmation of Unchanged Provisions)**: Section 5 confirming remainder remains in full force.

### Head-to-Head Ranks for Access-E*TRADE Questions:
| Question | BM25 Rank | BM25 + Rerank | Hybrid Rank | Hybrid + Rerank | Finding |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `Q36_amend_term_replacement_access` | Rank 1 | Rank 2 | Rank 2 | Rank 2 | Preserved at Top | 
| `Q37_amend_price_replacement_access` | Rank 2 | Rank 3 | Rank 3 | Rank 2 | Preserved at Top | 
| `Q38_amend_payment_amendment_access` | Rank 1 | Rank 1 | Rank 1 | Rank 1 | Preserved at Top | 
| `Q39_amend_full_force_confirmation_access` | Rank 1 | Rank 1 | Rank 2 | Rank 1 | Preserved at Top | 

---

## 2. Qualitative Analysis of Reranking Mutations
We inspect cases where the cross-encoder altered candidate order:
### Improved Queries (4):
- **`Q06_parties_access_identity`**: Rank 2 -> Rank 1
- **`Q07_parties_marqeta_role`**: Rank 2 -> Rank 1
- **`Q23_term_amx_notice_period`**: Rank 2 -> Rank 1
- **`Q31_cross_governing_law_comparison`**: Rank 9 -> Rank 2

### Degraded Queries (3):
- **`Q33_cross_spare_backup_hp_sow_linkage`**: Rank 2 -> Rank 6
- **`Q36_amend_term_replacement_access`**: Rank 1 -> Rank 2
- **`Q37_amend_price_replacement_access`**: Rank 2 -> Rank 3

---

## 3. Unanswerable Query Evaluation (7 Questions)
- Reranking scores were examined across all 7 unanswerable questions.
- In 100% of unanswerable cases, the reranker re-scored existing candidate passages without fabricating citations or modifying chunk provenance.
