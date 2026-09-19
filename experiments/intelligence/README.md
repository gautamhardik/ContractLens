# Contract Intelligence & Hybrid Extraction Report (Phase 5 & 6)

**Evaluation Date**: 2026-09-19  
**Deliverables Evaluated**:
- Structured Intelligence Schema: [`src/models/intelligence.py`](file:///c:/Users/hiten/Downloads/ContractLens/src/models/intelligence.py)
- Hybrid Extraction Engine: [`src/ingestion/extractor.py`](file:///c:/Users/hiten/Downloads/ContractLens/src/ingestion/extractor.py)
- Benchmark JSON: [`experiments/intelligence/benchmark_results.json`](file:///c:/Users/hiten/Downloads/ContractLens/experiments/intelligence/benchmark_results.json)

---

## 1. Executive Summary

Phase 5 & 6 establishes the **structured contract-intelligence layer** built on top of `CanonicalDocument`. In accordance with the Master Directive, extraction follows a **hybrid, evidence-grounded strategy**:
1. **Deterministic extraction** handles structured, pattern-bound fields (parties, effective dates, contract types, Net payment terms, notice days, and amendment modifications).
2. **Mandatory Provenance**: Every extracted fact retains an `EvidenceReference` pointer (`document_id`, `page_number`, `block_id`, `bbox`) tying it directly to original PDF coordinates.
3. **No Hallucinations / Explicit Missing States**: If a field is not present or redacted (e.g. `[*****]` termination notice in `Turtle Beach`), it is represented explicitly as `is_found = False` with a typed reason, rather than guessing.

---

## 2. Extraction Architecture by Target Field

| Target Field | Extraction Method | Normalization Applied | Provenance Retained | Handling for Missing / Redacted Data |
| :--- | :--- | :--- | :---: | :--- |
| **Contract Type** | Deterministic Regex on Title / Preamble blocks | Normalized to 9 standard archetypes (MSA, Amendment, Supply, License, DPA, etc.) | Yes (`bbox` of title block) | `ExtractedField.not_found("contract_type")` |
| **Parties** | Regex over Preamble & Recital entity cues | Corporate suffix trimming (Inc., LLC, Corp., Ltd.) | Yes (Preamble block) | Empty list if preamble is missing |
| **Effective Date** | Regex over Preamble cues ("effective as of", "dated") | Normalized date string (e.g. "June 1, 2005", "October 6, 2015") | Yes (Physical page & block) | Explicit `is_found = False` (e.g. in amendments effective upon last signature) |
| **Expiration Date** | Regex on Term & Expiration sections | Normalized date string | Yes (`bbox` of Term block) | Explicit `not_found` (most MSAs have relative terms or evergreen renewals) |
| **Renewal Language**| Regex on successive term cues ("automatic renewal", "successive terms") | Flagged as "Automatic / Successive Renewal Detected" | Yes (Exact clause block) | `not_found` |
| **Governing Law** | Regex on jurisdiction clauses ("laws of the State of X") | Normalized State/Province jurisdiction (e.g. "Delaware", "Texas", "California") | Yes (Closing provisions block) | `not_found` |
| **Payment Terms** | Regex on Net payment cues ("within 30 days of receipt", "Net 45") | Normalized integer `payment_days` (30, 45, 60) | Yes (Payment section block) | `not_found` |
| **Termination Notice**| Regex on notice cues ("at least 30 days prior written notice") | Normalized integer `notice_days` (30, 60, 90) & termination type | Yes (Termination block) | Explicit `not_found` when redacted (e.g. `[*****]` in `Turtle Beach`) |
| **Amendment Facts** | Deterministic structural diffing cues ("shall be deleted in its entirety", "amended by adding") | Action enum (`DELETE_AND_REPLACE`, `ADD_COVERAGE`, `CONFIRM_FULL_FORCE`) | Yes (Exact modification block) | Empty list for non-amendment contracts |

---

## 3. Gold-Set & Benchmark Results

### Core Representative Contracts

| Document ID | Agreement | Type Extracted | Effective Date | Governing Law | Payment Terms | Termination Notice | Amendment Facts |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **`doc_03`** | `Access-E*TRADE MSA` | Master Services Agreement | June 1, 2005 (P1) | Delaware (P12) | Due within 30 days (P3) | 30 days notice (P2) | 0 (Base MSA) |
| **`doc_02`** | `Access-E*TRADE Amendment` | Amendment | None (Upon signature) | None (Incorporated) | Due within 30 days (P2) | None stated | **3 distinct facts** |
| **`doc_13`** | `Spare Backup - HP MSA+SOW` | Standard Services + SOW | None (Preamble blank) | None (Schedule ref) | None found | 30 days prior notice (P9) | 0 |
| **`doc_16`** | `Square-Marqeta MSA` | Master Services Agreement | None (Filed exhibit) | California (P28) | Net 30 days (P4) | None found | 0 |
| **`doc_09`** | `SCYX - GSK DPA Provisions` | Exclusive License / DPA | March 30, 2023 (P1) | Delaware (P95) | Net 60 days (P45) | None found | 0 |
| **`doc_10`** | `Sabre-DXC MSA` (176p) | Amended & Restated MSA | August 1, 2020 (P1) | Texas (P88) | None (Custom schedule)| 30 days prior notice (P42)| 0 |

---

## 4. Ground Truth Amendment Representation: `Access-E*TRADE`

In the dedicated ground-truth test case ([`tests/test_intelligence_extraction.py`](file:///c:/Users/hiten/Downloads/ContractLens/tests/test_intelligence_extraction.py)), the extractor represented the 3 core modification actions declared in the amendment:
1. **Fact 1 (`DELETE_AND_REPLACE`)**: Deletes Section 1.2 (*Price*) and substitutes a revised pricing schedule.
2. **Fact 2 (`ADD_COVERAGE`)**: Amends Section 15.4 by adding mandatory Errors & Omissions insurance coverage of $2,000,000.
3. **Fact 3 (`CONFIRM_FULL_FORCE`)**: Confirms that unamended provisions of the base MSA remain in full force and effect.
4. **Payment Term Provenance**: Extracted the amended payment clause on Page 2: *"Invoices are payable in US dollars and undisputed invoices are due within thirty days of the date of receipt"* (Normalized: `payment_days = 30`).

---

## 5. Failure / Ambiguity Handling

- **Redacted Information**: In `Turtle Beach-Foxconn MSA` (`doc_17`), the termination notice period is redacted (`upon no less than [*****] prior written notice`). The extractor returned `is_found = False` rather than guessing.
- **Undated SEC Exhibits**: Regulatory filings like `Square-Marqeta` often omit the calendar date on Exhibit 10.14 (`entered into as of ______`). The extractor returns `is_found = False` without fabricating a placeholder date.
- **Conflicting Candidates Schema**: The `ConflictedField` model allows downstream semantic reconciliation when multiple dates appear (e.g. execution date vs. effective date).
