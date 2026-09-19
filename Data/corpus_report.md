# ContractLens — Comprehensive Corpus Audit Report

**Phase 1 Deliverable | Date: 2026-09-19**  
**Audit Target**: `Data/raw/` (Immutable Source Corpus)  
**Manifest Path**: [`Data/corpus_manifest.json`](file:///c:/Users/hiten/Downloads/ContractLens/Data/corpus_manifest.json)

---

## 1. Corpus Overview

The ContractLens development and evaluation corpus consists of real-world commercial contracts filed with the U.S. Securities and Exchange Commission (SEC) via the EDGAR system. These agreements represent sophisticated bilateral commercial transactions across technology services, hardware manufacturing, telecommunications, financial services, and intellectual property licensing.

- **Total Documents**: 18 files
- **Expected Document Count**: 18 files (per project context)
- **Discrepancy**: **None (0)**. The physical filesystem inventory perfectly matches the documented baseline.
- **Total Corpus Page Count**: 696 pages
- **Total Corpus Character Count**: 2,058,958 characters (~2.06 MB raw text)
- **Total Storage Size**: 19,833,264 bytes (~18.91 MB)
- **Text Extractability**: 100% digital vector PDF (0 scanned image-only documents; OCR is **not** required for baseline text extraction).

---

## 2. Comprehensive File Inventory

| ID | Filename | Pages | Size (Bytes) | Chars | Tables Detected | Sigs | Exh/Sched | Complexity | Primary Document Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `doc_01` | `AMX–Best Circuit Boards Supply Agreement.pdf` | 7 | 157,602 | 19,422 | 0 | Yes | Yes | **LOW** | Supply Agreement |
| `doc_02` | `Access–E-TRADE Amendment.pdf` | 3 | 163,352 | 6,806 | 0 | Yes | Yes | **LOW** | Amendment |
| `doc_03` | `Access–E-TRADE MSA.pdf` | 14 | 213,067 | 40,889 | 0 | Yes | Yes | **LOW** | Master Services Agreement |
| `doc_04` | `Colocation Master Services Agreement (2).pdf` | 83 | 2,072,198 | 243,590 | 2 | Yes | Yes | **HIGH** | Master Services Agreement |
| `doc_05` | `GE Power & Water–TPI Supply Agreement.pdf` | 74 | 936,452 | 199,739 | 2 | Yes | Yes | **HIGH** | Supply Agreement |
| `doc_06` | `Guidehouse Managed Services MSA.pdf` | 44 | 604,341 | 130,687 | 0 | Yes | Yes | **MEDIUM** | Master Services Agreement |
| `doc_07` | `JPMorgan Supplier MSA Amendment.pdf` | 10 | 268,770 | 33,117 | 10 | Yes | Yes | **MEDIUM** | Amendment |
| `doc_08` | `Karman Topco – First Amendment to Limited Partnership Agreement.pdf` | 4 | 141,854 | 4,809 | 0 | Yes | No | **LOW** | Amendment |
| `doc_09` | `SCYX – Data Processing Agreement provisions.pdf` | 129 | 5,101,283 | 394,156 | 132 | Yes | Yes | **HIGH** | Exclusive License / DPA Provisions |
| `doc_10` | `Sabre–DXC Amended & Restated MSA.pdf` | 176 | 2,186,844 | 435,323 | 8 | Yes | Yes | **HIGH** | Amended & Restated MSA |
| `doc_11` | `Software License Agreement – ACCESS.pdf` | 93 | 1,286,881 | 228,475 | 0 | Yes | Yes | **HIGH** | Software License Agreement |
| `doc_12` | `Software License Agreement – Robertson Technologies.pdf` | 13 | 371,782 | 40,787 | 0 | Yes | Yes | **LOW** | Software License Agreement |
| `doc_13` | `Spare Backup – Hewlett-Packard Standard Services Agreement + SOW.pdf` | 29 | 1,484,924 | 86,853 | 36 | Yes | Yes | **MEDIUM** | Master Services Agreement + SOW |
| `doc_14` | `Sun Microsystems Master Supply Agreement.pdf` | 18 | 331,931 | 84,727 | 0 | Yes | Yes | **MEDIUM** | Master Supply Agreement |
| `doc_15` | `TNS Smart Network – ABM Processing Agreement.pdf` | 12 | 265,285 | 50,711 | 0 | Yes | Yes | **LOW** | Processing Agreement |
| `doc_16` | `The SEC filing for Square-Marqeta.pdf` | 63 | 1,306,245 | 169,297 | 23 | Yes | Yes | **HIGH** | Master Services Agreement |
| `doc_17` | `Turtle Beach–Foxconn MSA.pdf` | 16 | 390,489 | 57,188 | 0 | Yes | Yes | **LOW** | Master Services Agreement |
| `doc_18` | `VIAC Non-Disclosure Agreement (2025).pdf` | 9 | 217,613 | 20,177 | 0 | Yes | Yes | **LOW** | Non-Disclosure Agreement |

---

## 3. Document Type Distribution

| Archetype | Count | Percentage | Representative Files |
| :--- | :--- | :--- | :--- |
| **Master Services Agreement (MSA)** | 7 | 38.9% | Access-E-TRADE MSA, Guidehouse MSA, Square-Marqeta MSA, Turtle Beach-Foxconn MSA, Colocation MSA |
| **Amendments / Variations** | 3 | 16.7% | Access-E-TRADE Amendment, JPMorgan Supplier MSA Amendment, Karman Topco First Amendment |
| **Supply Agreements** | 3 | 16.7% | AMX-Best Circuit Boards, GE Power & Water-TPI, Sun Microsystems Master Supply |
| **Software License Agreements (SLA/EULA)** | 2 | 11.1% | ACCESS (PalmSource/Palm), Robertson Technologies (Telemedicine Africa) |
| **Amended & Restated Master Agreement** | 1 | 5.6% | Sabre-DXC Amended & Restated MSA (Major IT outsourcing) |
| **License / Data Processing Provisions** | 1 | 5.6% | SCYNEXIS / GlaxoSmithKline Exclusive License & DPA Provisions |
| **Standard Services Agreement + SOW** | 1 | 5.6% | Spare Backup - Hewlett-Packard Standard Services Agreement + SOW |
| **Non-Disclosure Agreement (NDA)** | 1 | 5.6% | Venerable Investment Advisers / VIAC Mutual NDA (2025) |
| **Transaction Processing Agreement** | 1 | 5.6% | TNS Smart Network - Vencash ABM Processing Agreement |

---

## 4. Page-Count & Length Distribution

- **Short Agreements (< 15 pages)**: 8 documents (44.4%)
  - Median page count: ~10 pages. Includes NDAs, standard amendments, concise MSAs (`Turtle Beach-Foxconn`, `Access-E-TRADE`).
- **Medium Agreements (15 – 50 pages)**: 4 documents (22.2%)
  - Range: 16 to 44 pages. Includes `Guidehouse MSA` (44p), `Spare Backup-HP` (29p), `Sun Microsystems` (18p).
- **Long / Complex Portfolios (> 50 pages)**: 6 documents (33.3%)
  - Range: 63 to 176 pages. Includes `Sabre-DXC MSA` (176p), `SCYX-GSK` (129p), `ACCESS License` (93p), `Colocation MSA` (83p), `GE Power & Water` (74p), `Square-Marqeta` (63p).

---

## 5. Extraction Quality & PDF Rendering Sample

- **Native Text Availability**: 100% of the 18 PDF files contain clean digital text layers rendered via Skia/PDF from SEC HTML filings.
- **Font & Character Encodings**: Character streams are well-formed UTF-8. Non-breaking spaces and hyphens/dashes (`\u2013`, `\u2014`) are present in headings and filenames.
- **Reading Order**: Sequential reading order is clean and predictable across standard single-column legal bodies. Multi-column text is rare in the core text, but present in signature blocks and schedule exhibits.
- **SEC Artifacts & Noise**:
  - EDGAR filing header banners appear on page 1 of almost all documents (e.g., `EX-10.1 2 dex101.htm`, `CONFIDENTIAL INFORMATION REDACTED...`, SEC URLs).
  - Skia print footers appear with timestamps and URLs (e.g., `9/19/26, 9:57 AM Amendment to Master Services Agreement https://www.sec.gov/...`).
  - **Ingestion Implication**: Header and footer filtering logic will be required to avoid indexing transient filing timestamps and URLs into semantic embeddings.

---

## 6. Structural Characteristics & Layout Elements

1. **Numbered Clause Hierarchies**:
   - 17 of 18 documents employ formal alphanumeric or decimal numbering schemes (e.g., `Section 1.1`, `Article IV`, `3.2(a)(ii)`).
   - Paragraph and sub-clause numbering provides ideal anchor points for canonical block segmentation.
2. **Tables**:
   - Heavy table usage is concentrated in 6 files: `SCYX` (132 tables), `Spare Backup-HP` (36 tables), `Square-Marqeta` (23 tables), `JPMorgan Amendment` (10 tables), `Sabre-DXC` (8 tables), and `Colocation MSA` (2 tables).
   - Tables represent pricing tiers, SLA credit matrices, service schedules, and data processing specifications.
3. **Signatures**:
   - Explicit execution signature blocks (`IN WITNESS WHEREOF`, `By:`, `Title:`) were detected in all 18 documents.
4. **Exhibits, Schedules & Appendices**:
   - 17 of 18 documents contain subordinate exhibits, schedules, statements of work, or service level agreements appended after the main terms.
5. **Redaction Markers**:
   - SEC confidential treatment redaction tokens (`[***]`, `[*]`, `[*****]`) appear frequently in pricing schedules, fee formulas, and specific intellectual property terms across at least 8 contracts. The extraction pipeline must treat these tokens gracefully without failing syntactic validation.

---

## 7. Document Relationships Discovered

### A. Direct Intra-Corpus Pair (Golden Ground Truth for Version Intelligence)
- **Base Agreement**: `Access-E-TRADE MSA.pdf` (`doc_03`)
  - Effective Date: June 1, 2005.
  - Parties: Access Worldwide Communications, Inc. and E*TRADE Financial Corporation.
- **Superseding Amendment**: `Access-E-TRADE Amendment.pdf` (`doc_02`)
  - Execution Date: January 17, 2008.
  - Verifiable Relationship:
    - Recital: *"WHEREAS, Access and Company entered into a Master Services Agreement effective June 1, 2005 (the 'Agreement')."*
    - **Section 1**: Deletes Section 1.2 (*Price*) and substitutes a revised pricing schedule.
    - **Section 2**: Deletes Section 3 (*Term*) and ties the Initial Term to an "Initial Services Savings Amount".
    - **Section 3**: Deletes Section 6 (*Payment*) and replaces payment provisions (Net 30, monthly billing, agent hourly tiers).
    - **Section 4**: Amends Section 15.4 by mandating Errors & Omissions insurance of $2,000,000.
    - **Section 5**: Confirms all other provisions remain in full force and effect.
  - **Significance**: Provides a complete, verifiable baseline for testing Version Comparison, Section Alignment, and Obligation Impact Analysis.

### B. Unilateral / External Amendment Relationships
- `JPMorgan Supplier MSA Amendment.pdf` (`doc_07`): Amends external base agreement `Master Services Agreement CW232350` (Dated January 4, 2008) with JPMorgan Chase Bank, N.A.
- `Karman Topco – First Amendment...pdf` (`doc_08`): Amends external base agreement `Eighth Amended and Restated Limited Partnership Agreement of Karman Topco L.P.` (Dated September 7, 2020).
- `Sabre–DXC Amended & Restated MSA.pdf` (`doc_10`): Supersedes and replaces a prior long-term IT infrastructure agreement between Sabre and DXC Technology Services LLC.

---

## 8. High-Complexity / Difficult Documents

1. **`doc_10` — `Sabre-DXC Amended & Restated MSA.pdf` (176 pages, 435K chars)**
   - *Challenges*: Extreme length, multi-tier exhibit structure, cross-references across schedules, extensive redactions, complex governance clauses.
2. **`doc_09` — `SCYX – Data Processing Agreement provisions.pdf` (129 pages, 394K chars)**
   - *Challenges*: 132 embedded tables, international data transfer clauses (SCCs), technical security measures matrices.
3. **`doc_11` — `Software License Agreement – ACCESS.pdf` (93 pages, 228K chars)**
   - *Challenges*: Dense IP definitions, patent grants, source code escrow obligations, complex Royalties schedules.
4. **`doc_04` — `Colocation Master Services Agreement (2).pdf` (83 pages, 243K chars)**
   - *Challenges*: Facility power/space SLAs, complex liquidated damages, maintenance outage windows.
5. **`doc_16` — `The SEC filing for Square-Marqeta.pdf` (63 pages, 169K chars)**
   - *Challenges*: Complex transaction volume tiers, payment card network rules, interchange fee schedules embedded in 23 tables.

---

## 9. Corpus Strengths & Coverage

- **Real-World Authenticity**: Contains actual market-standard commercial legal drafting, not sanitized synthetic text.
- **Diverse Agreement Archetypes**: Strong representation of service agreements (MSAs), manufacturing/supply contracts, software licenses, NDAs, and amendments.
- **Verifiable Amendment Delta**: The presence of both `Access-E-TRADE MSA` and its subsequent `Amendment` provides an un-fabricated, end-to-end evaluation scenario for version intelligence and change impact tracking.
- **Rich Obligation Diversity**: Documents span monthly reporting requirements, insurance maintenance, audit rights, payment terms (Net 30/Net 45), termination notice windows (30/60/90 days), and SLA remedy triggers.

---

## 10. Corpus Limitations

- **Single Intra-Corpus Amendment Pair**: Only one paired base-and-amendment set (`Access-E-TRADE`) exists within the 18 files. The other amendments (`JPMorgan`, `Karman Topco`) refer to external base agreements not present in the directory.
  - *Engineering Implication*: For multi-version comparison benchmarks, `Access-E-TRADE` is the primary ground truth. For cross-contract queries, the remaining 16 standalone contracts provide rich portfolio variety.
- **Confidential Information Redactions**: Several commercial schedules have redactions (`[***]`). Evaluation queries should target unredacted operational covenants and notice terms rather than redacted dollar amounts.

---

## 11. Implications for Phase 2 (Document Ingestion Benchmark)

The audit surfaces clear, empirical requirements that Phase 2 must evaluate:

1. **Parser Selection**:
   - Because 100% of the documents have clean digital text streams, heavy OCR (e.g., Tesseract) is **unnecessary**.
   - The primary differentiator between parsers (e.g., `PyMuPDF` vs. `pdfplumber` vs. `pypdf`) will be **table structure preservation**, **reading order through SEC headers**, and **precise bounding box / coordinate extraction** for click-to-cite evidence drawers.
2. **SEC Filing Header/Footer Stripping**:
   - Ingestion must strip running HTML headers (e.g., `EX-10.1`, `sec.gov/Archives/...`) and page number lines so that embeddings index only authentic contractual text.
3. **Table Handling**:
   - 6 contracts contain critical pricing and SLA matrices in table format. Ingestion must evaluate whether Markdown or structured JSON table representations preserve tabular relationships better for downstream RAG.
4. **Canonical Block Model**:
   - A unified schema containing `document_id`, `page_number`, `section_number`, `section_title`, and `block_type` (heading, paragraph, table, list) will cleanly capture the structural patterns identified in this audit.
