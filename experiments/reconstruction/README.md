# Structural Reconstruction Evaluation Report (Phase 3 & 4)

**Evaluation Date**: 2026-09-19  
**Deliverables Evaluated**:
- Canonical Document Schema: [`src/models/canonical.py`](file:///c:/Users/hiten/Downloads/ContractLens/src/models/canonical.py)
- Structural Reconstructor: [`src/ingestion/reconstructor.py`](file:///c:/Users/hiten/Downloads/ContractLens/src/ingestion/reconstructor.py)
- Benchmark JSON: [`experiments/reconstruction/evaluation_results.json`](file:///c:/Users/hiten/Downloads/ContractLens/experiments/reconstruction/evaluation_results.json)

---

## 1. Executive Summary

Phase 3 and Phase 4 establish the **provenance-first canonical document layer** of ContractLens. The system successfully bridges raw PDF byte streams and downstream intelligence extraction by reconstructing raw pages into strongly typed, hierarchically organized, coordinate-bound data structures without destroying or altering source text.

### Key Results Across Representative Benchmark Documents

| Document ID | Test Document | Pages | Total Blocks | Clean Blocks | SEC Noise Blocks | Tables Tagged | Sections Detected | Bounding Box Completeness | Latency |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **`doc_02`** | `Access-E-TRADE Amendment` (Short GT) | 3 | 47 | 39 | 8 (17.0%) | 0 | 1 | **100%** | 0.21s |
| **`doc_13`** | `Spare Backup - HP Standard Services` | 29 | 480 | 421 | 59 (12.3%) | 65 | 0* | **100%** | 7.33s |
| **`doc_16`** | `The SEC filing for Square-Marqeta` | 63 | 675 | 536 | 139 (20.6%) | 64 | 1* | **100%** | 27.91s |
| **`doc_09`** | `SCYX - DPA Provisions` (132 Tables) | 129 | 1,225 | 965 | 260 (21.2%) | 967** | 32 | **100%** | 173.27s |
| **`doc_10`** | `Sabre-DXC MSA` (176p Stress Test) | 176 | 2,653 | 2,140 | 513 (19.3%) | 22 | 37 | **100%** | 30.77s |

*\*Note on Section Detection*: Documents formatted with inline clause titles (e.g. `1.2 Price.` inline with the paragraph text) are preserved as paragraphs with exact text intact, rather than standalone heading blocks. This is an explicit conservative choice to avoid falsely segmenting text.  
*\*\*Note on Tables in SCYX*: Complex multi-page schedule matrices in `SCYX` generate sub-block cell groups, all tagged with block type `table` and containing full row/column data.

---

## 2. Canonical Schema Architecture

The canonical document representation is defined via typed Pydantic models in `src/models/canonical.py`:

```
CanonicalDocument
 ├── document_id
 ├── filename
 ├── file_size
 ├── page_count
 ├── sections [ CanonicalSection: section_number, section_title, block_ids ]
 └── pages [ CanonicalPage ]
       ├── page_number (1-indexed)
       ├── width, height
       └── blocks [ CanonicalBlock ]
             ├── block_id (e.g. doc_02_p001_b08)
             ├── reading_order (0-indexed sequence)
             ├── block_type (heading, paragraph, list_item, table, signature_block, sec_noise)
             ├── bbox (BoundingBox: x0, y0, x1, y1)
             ├── raw_text (exact unmutated extracted string)
             ├── normalized_text (whitespace-normalized for matching)
             ├── section_number & section_title context
             ├── is_sec_noise & noise_reason
             └── table_data (TableData: num_rows, num_cols, headers, rows, raw_matrix)
```

---

## 3. Provenance & Evidence Tracking

The schema guarantees deterministic provenance via `CanonicalBlock.to_evidence_ref(filename)`:
- Returns an `EvidenceReference` object containing:
  - `document_id`: Unique identifier (e.g. `doc_02`)
  - `page_number`: Exact physical PDF page (1-indexed)
  - `block_id`: Stable identifier (e.g. `doc_02_p001_b08`)
  - `bbox`: Geometric coordinates `(x0, y0, x1, y1)` in PDF points
  - `section_number` / `section_title`: Inherited clause hierarchy
- **Zero Text Mutation**: Downstream citation drawers can highlight the original text directly on the PDF canvas using `bbox` without text mismatch.

---

## 4. SEC Noise Tagging Quality

- **Noise Detection Rate**: Between **12.3% and 21.2%** of raw blocks in SEC filings were identified as filing noise.
- **Classification Reasons**:
  - `sec_header_zone`: Top-of-page EDGAR exhibit markers (`EX-10.*`) and web print timestamps.
  - `sec_footer_zone`: Bottom-of-page printed URLs (`https://www.sec.gov/...`) and page sequence counters.
- **Preservation Principle**: Noise blocks are **never dropped** from the canonical document; they remain in `page.blocks` with `is_sec_noise = True` and `block_type = BlockType.SEC_NOISE`, allowing downstream RAG chunking to filter them via `doc.get_all_blocks(include_noise=False)`.

---

## 5. Known Limitations & Heuristic Boundaries

1. **Inline Clause Headings**: Many contracts format clauses as `1. Term. This Agreement shall commence...` rather than having `1. Term` on a separate line. The reconstructor prioritizes preserving complete paragraph boundaries rather than splitting inline sentences.
2. **Signature Blocks**: Multi-column signature blocks with side-by-side company names are grouped as sequential `signature_block` types; downstream party extraction should parse signature columns using coordinate `x0` offsets.
3. **Table-Dense Document Latency**: On documents with >100 pages and >100 tables (`SCYX`), running table cell extraction page-by-page takes ~173 seconds. Future optimizations can cache the parsed `CanonicalDocument` to JSON.
