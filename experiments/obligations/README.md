# ContractLens: Obligation, Temporal & Lifecycle Benchmark (Phase 7–9)

## Executive Summary

Phase 7–9 shifts ContractLens from passive text extraction ("What does the contract say?") to active operational commitments ("What must happen, who must do it, when, under what trigger, and where does the evidence come from?").

This experiment benchmarks the deterministic-first obligation extractor, temporal classification engine, and lifecycle milestone generator across 6 target contracts of varying structural complexity and length.

---

## 1. Methodology & Verification Guarantees

1. **Mandatory Provenance**: Every extracted obligation and lifecycle event carries an immutable `EvidenceReference` with `document_id`, `page_number`, `block_id`, and bounding box coordinates `[x0, y0, x1, y1]`.
2. **Zero Completion Status Fabrication**: In accordance with system constraints, without live external operational ERP/billing integrations, all contract obligation completion states remain strictly `UNKNOWN`. The system does not invent real-world compliance.
3. **No Hallucinated Anchor Dates**:
   - `RELATIVE_OFFSET` and `EVENT_RELATIVE` obligations maintain `is_resolved = False` when the triggering event (e.g. invoice receipt, breach discovery, notice delivery) has not occurred or has no concrete timestamp.
   - `calculated_date` is computed only when an explicit calendar anchor date is provided.
4. **Recurrence Without Infinite Materialization**: Recurring obligations (e.g., monthly service reports, annual audits) store recurrence frequency rules (`RecurrenceRule`) rather than generating infinite future date instances.

---

## 2. Empirical Benchmark Results

Evaluated across 6 diverse contracts representing 161 total pages:

| Document ID | Contract Title | Page Count | Total Extracted Obligations | Lifecycle Milestones | Top Temporal Classifications | Key Resolved Parties / Actors |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **doc_03** | Access–E\*TRADE MSA | 14 | 83 | 5 | UNSPECIFIED (68), ONGOING (7), CONDITIONAL (6), FIXED_DATE (1), RECURRING (1) | The Parties, Either Party, Customer, Contractor |
| **doc_02** | Access–E\*TRADE Amendment | 3 | 12 | 6 | UNSPECIFIED (10), FIXED_DATE (2) | The Parties, unresolved (section amendment clauses) |
| **doc_13** | Turtle Beach–Foxconn MSA | 37 | 179 | 3 | UNSPECIFIED (142), ONGOING (18), CONDITIONAL (15), RELATIVE_OFFSET (2) | Supplier, Customer, The Parties |
| **doc_01** | AMX–Best Circuit Boards Supply Agmt | 7 | 26 | 5 | UNSPECIFIED (18), ONGOING (4), CONDITIONAL (3), RELATIVE_OFFSET (1) | AMX, Best Circuit Boards, Supplier, Customer |
| **doc_15** | Spare Backup–HP MSA + SOW | 37 | 158 | 4 | UNSPECIFIED (118), ONGOING (22), CONDITIONAL (12), RECURRING (3), RELATIVE (3) | HP, Spare Backup, Contractor, Vendor |
| **doc_16** | Square–Marqeta Processing Agmt | 63 | 321 | 5 | UNSPECIFIED (241), ONGOING (38), CONDITIONAL (24), RELATIVE (12), RECURRING (6) | Square, Marqeta, Bank, The Parties |

**Total Obligations Extracted Across Sample**: 779  
**Provenanced Coordinate Coverage**: 100.0%  
**Fabricated Real-World Dates**: 0  

---

## 3. Ground-Truth Analysis: Access–E\*TRADE Amendment Pair

The Access–E\*TRADE pair serves as our primary ground truth:

1. **Section 1.2 (Price)**: Successfully extracted as an amendment lifecycle milestone (`DELETE_AND_REPLACE`) tied to Page 1, Block 14.
2. **Section 3 (Term)**: Successfully identified as an amendment milestone with initial commencement date `June 1, 2005` and continuing until the Service Savings Amount threshold is met.
3. **Section 6 (Payment Terms)**: Successfully identified Net 30 payment terms (`Invoice received + 30 days`) with `offset_days = 30`, `anchor_event = "invoice_received"`, and `is_resolved = False`.
4. **Section 15.4 (Insurance)**: Successfully identified as an ongoing insurance obligation covenant with amendment milestone `ADD_COVERAGE` adding $2,000,000 E&O coverage.

---

## 4. Failure Mode & Edge Case Testing

- **Redacted Information**: In `Turtle Beach-Foxconn MSA` (doc_13), termination notice days were redacted by SEC filings as `[*****]`. The engine correctly returned `notice_days = None` and kept `is_found = False` without fabricating a notice period.
- **Ambiguous Actor**: Passively phrased covenants (e.g., *"strict confidentiality shall be maintained"*) correctly resolve to `actor = "unresolved"` rather than making an arbitrary guess.
- **Complex Trigger Conditions**: Clauses beginning with *"If a force majeure event occurs, party shall notify..."* are parsed as `CONDITIONAL` with the triggering condition extracted separately from the timing offset.
