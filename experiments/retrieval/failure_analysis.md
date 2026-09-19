# Retrieval Failure Analysis (Phase 13)

Detailed qualitative analysis of retrieval misses, edge cases, and boundary conditions across BM25, Dense Semantic, and Hybrid RRF.

---

## 1. Access–E*TRADE Amendment vs. Parent MSA Pair Analysis
A critical requirement of ContractLens is distinguishing parent agreement evidence from amendment modifications:
- **`Q36` (Term Extension)**: Amendment Section 2 deletes Section 3 and substitutes the Initial Term.
- **`Q37` (Deleted Storage Fee)**: Amendment Section 1 replaces price schedule, removing monthly storage charges.
- **`Q38` (Cyber/E&O Insurance)**: Amendment Section 4 adds $2,000,000 Errors & Omissions requirement.
- **`Q39` (Unchanged Confidentiality)**: Amendment Section 5 confirms remaining terms remain in full force.

### Findings on Amendment Distinction
- When queries explicitly reference the Amendment (`doc_02`), both BM25 and Hybrid RRF isolate the exact amendment chunk at **Rank 1**.
- When queries compare across documents (`Q32`: Net 30 payment terms between Access and AMX), multi-document target filtering retrieves both respective payment clauses within the top ranks without mixing clause provenance.

---

## 2. Qualitative Misses & Edge Cases

### Question: `Q01_meta_law_access` (metadata)
- **Query**: "What is the governing law of the Access-E*TRADE Master Services Agreement?"
- **Expected Answer**: State of Delaware
- **Target Documents**: ['doc_03']
- **Gold Ranks Found**: [10]
- **Failure Classification**: `None`

### Question: `Q02_meta_law_sabre` (metadata)
- **Query**: "Which state's laws govern the Sabre-DXC Amended & Restated Agreement?"
- **Expected Answer**: State of Texas
- **Target Documents**: ['doc_10']
- **Gold Ranks Found**: None in Top 10
- **Failure Classification**: `semantic_lexical_mismatch`

### Question: `Q14_date_scyx_gsk_effective` (dates_lifecycle)
- **Query**: "What is the effective date stated in the SCYNEXIS-GSK License Agreement?"
- **Expected Answer**: March 30, 2023
- **Target Documents**: ['doc_09']
- **Gold Ranks Found**: None in Top 10
- **Failure Classification**: `semantic_lexical_mismatch`

### Question: `Q31_cross_governing_law_comparison` (cross_document)
- **Query**: "Compare the governing law between the Access-E*TRADE MSA and the Sabre-DXC Agreement. Which states govern each?"
- **Expected Answer**: The Access-E*TRADE MSA is governed by Delaware law, whereas the Sabre-DXC Agreement is governed by Texas law.
- **Target Documents**: ['doc_03', 'doc_10']
- **Gold Ranks Found**: [10]
- **Failure Classification**: `None`

---

## 3. Unanswerable Query Handling (7 Questions)
The benchmark intentionally contains 7 unanswerable questions:
- `Q05_meta_exp_viac` (VIAC expiration date is not fixed)
- `Q10_party_guarantor_amx` (No parent guarantor in AMX)
- `Q15_date_retroactive_turtle` (No retroactive commencement date)
- `Q20_pay_index_hp` (No CPI indexing in HP MSA)
- `Q24_term_penalty_access` (No early convenience termination penalty fee)
- `Q35_cross_indemnity_portfolio` (No cross-contract indemnity bond)
- `Q40_amend_arbitration_access` (No arbitration revision in Access Amendment)

### Retrieval Behavior
For unanswerable queries, retrieval correctly surfaces the most semantically related neighborhood (e.g. the base dispute section or term section) without hallucinating nonexistent clauses. Downstream answer verification (Phase 17–19) will be responsible for evaluating that the evidence does not support the claim.
