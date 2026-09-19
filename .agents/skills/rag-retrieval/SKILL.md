---
name: rag-retrieval
description: Guidelines for embedding generation, vector indexing, hybrid search, and clause reranking.
---

# RAG & Retrieval Skill

## When to Use
Use when implementing embedding models, vector database connections, hybrid search (BM25 + dense), or reranking pipelines.

## Critical Constraints
1. **Metadata Retention**: Chunks indexed into the vector store must preserve:
   - `document_name`
   - `page_number`
   - `section_header` / `clause_id`
   - `chunk_id`
2. **Hybrid Retrieval**: Dense search alone often misses exact section numbers or statutory legal definitions; design for hybrid lexical + dense retrieval.
3. **Traceability**: Retrieval results must always return the source page and surrounding context window for verification.
4. **No Premature Hardcoding**: Keep embedding provider and vector store decoupled via standard interfaces.

## Typical Workflow
1. Load processed chunks from `Data/processed/`.
2. Generate embeddings and populate index.
3. Run targeted query benchmarks (e.g., specific clause search, definition lookup).
4. Evaluate precision and citation correctness.
