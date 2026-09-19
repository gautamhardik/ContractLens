---
name: contract-ingestion
description: Guidelines for parsing and ingesting raw contract PDFs into structured representations.
---

# Contract Ingestion Skill

## When to Use
Use when implementing or modifying PDF document loading, text extraction, layout parsing, or chunking pipelines.

## Critical Constraints
1. **Immutability**: Never modify or write into `Data/raw/`. Write processed artifacts into dedicated directories (e.g., `Data/processed/`).
2. **Provenance Preservation**: Retain exact document identity, page numbers, and section headings on every extracted chunk or block.
3. **Dual Need**: Keep structured metadata extraction (dates, parties, amounts) distinct from text chunking for vector search.
4. **Tool Evaluation**: Benchmark parser choices (PyMuPDF, pdfplumber, etc.) on challenging layouts (tables, multi-column text) before finalizing.

## Typical Workflow
1. Read `docs/agent-context/DATASET.md` for document profiles.
2. Select target subset for ingestion testing.
3. Run extraction pipeline generating structured JSON or markdown with page/coordinate metadata.
4. Validate extraction fidelity (verify headers, tables, and page boundaries).
