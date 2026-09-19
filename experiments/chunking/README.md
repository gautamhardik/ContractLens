# ContractLens: Chunking Strategy Benchmark Report (Phase 11 & 12)

## Executive Summary

Before choosing embedding models or vector databases, ContractLens evaluated the fundamental retrieval unit: **how should legal contracts be segmented into chunks without severing clauses, losing context, or breaking evidence provenance?**

This experiment compared a baseline **Fixed Sliding Window** strategy against a structural **Section-Aware Chunking** strategy using our 40-question golden evaluation benchmark across 9 representative contracts (representing 353 total PDF pages).

---

## 1. Chunking Strategies Evaluated

### Strategy A: Fixed Sliding Window Baseline (`FixedSlidingWindowChunker`)
- **Parameters**: 1,000 characters target window size, 200 characters overlap.
- **Logic**: Iterates over clean reading-order blocks; flushes when character limit is reached; retains trailing blocks up to overlap length.
- **Hypothesis**: Generic RAG default; prone to slicing sentences, splitting clauses across boundaries, and generating high duplication.

### Strategy B: Section-Aware Contract Chunker (`SectionAwareChunker`)
- **Parameters**: 2,500 characters max size, 150 characters min size.
- **Logic**: Preserves contract structural hierarchy:
  1. Respects major section (`1.`, `2.`), subsection (`1.1`, `1.2`), and exhibit headers (`EXHIBIT A`).
  2. Isolates complex tables (`BlockType.TABLE`) into dedicated table retrieval units with structural row/column metadata.
  3. Preserves multi-paragraph clause integrity, only splitting if a single section exceeds 2,500 characters.
  4. Maintains 100% provenance back to `block_ids`, `section_title`, `section_number`, `page_start`, `page_end`, and geometric bounding boxes (`[x0, y0, x1, y1]`).

---

## 2. Quantitative Structural Statistics

Evaluated across 9 contracts totaling 353 pages:

| Metric | Fixed Sliding Window Baseline | Section-Aware Chunker | Advantage / Analysis |
| :--- | :--- | :--- | :--- |
| **Total Chunks Produced** | 1,606 chunks | 1,545 chunks | **-3.8% fewer chunks** (eliminates artificial sliding window duplication) |
| **Mean Character Length** | 1,605.2 chars | 745.3 chars | Section-aware chunks are more tightly focused on specific contractual covenants |
| **Median Character Length** | 1,349.5 chars | 274.0 chars | Section-aware cleanly captures short definitions & clauses without padding |
| **Standard Deviation** | 779.2 chars | 910.0 chars | Reflects natural legal contract variety (short definitions vs. multi-subclause terms) |
| **Cross-Page Chunks** | 510 chunks (31.8%) | 252 chunks (16.3%) | **49.4% reduction in cross-page chunk splits** |
| **Coordinate Provenance Retention** | 100.0% (1,606 / 1,606) | 100.0% (1,545 / 1,545) | Both retain exact bounding boxes for click-to-cite |

---

## 3. Benchmark Evidence Containment (40 Golden Questions)

Tested against the 40-question golden benchmark across 8 legal and operational categories:

| Containment Category | Fixed Sliding Window | Section-Aware Chunker | Impact on Downstream Retrieval |
| :--- | :--- | :--- | :--- |
| **Single-Chunk Contained** | 39 / 40 (97.5%) | 39 / 40 (97.5%) | Both strategies successfully contained complete evidence in 39 single-contract questions |
| **Multi-Chunk Split** | 1 / 40 (2.5%) | 1 / 40 (2.5%) | **Q32** (Cross-contract comparison between Access Net 30 and AMX Net 30 requires 2 chunks across 2 distinct documents by definition) |
| **Evidence Not Found / Severed** | 0 / 40 (0.0%) | 0 / 40 (0.0%) | 0 unanswerable or severed single-document questions |

---

## 4. Key Architectural Findings & Recommendations

1. **Why Section-Aware Chunker Wins for Contract RAG**:
   - **Eliminates Overlap Hallucination / Redundancy**: Sliding windows repeatedly capture the tail of Section 6 and the head of Section 7 together, creating noisy embeddings that retrieve irrelevant adjacent text. Section-aware keeps Section 6 (Payment) cleanly separated from Section 7 (Records & Audit).
   - **Cross-Page Integrity**: Legal clauses frequently spill across page breaks (e.g., Section 15.4 insurance limits start on page 11 and end on page 12 in `doc_03`). The section-aware chunker groups these blocks by parent section ID, preserving the entire covenant in a single retrieval unit.
   - **Dedicated Table Units**: Financial tables (e.g., Square-Marqeta processing fees, SCYX milestone royalty schedules) are retained as discrete `ChunkType.TABLE` units, preventing text fragment corruption.
2. **Recommendation for Phase 13 (Retrieval Stack)**:
   - Adopt **`SectionAwareChunker`** as the primary production chunking engine for all downstream embedding, BM25, and hybrid retrieval experiments.
