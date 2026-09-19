# Architecture

## Current Implementation Status
**None.** The repository currently contains no application code, no backend, no frontend, and no operational pipelines. Only raw contract data exists in `Data/raw/`.

---

## Planned Architecture

The envisioned ContractLens system consists of an end-to-end processing pipeline, a structured data layer, an evidence-backed agent, and a user interface.

```
[Contract Documents (PDFs)]
         ↓
 [Document Ingestion / Parsing Engine]
         ↓
 [Structure-Aware Extraction & Chunking]
         ↓
 [Embedding & Indexing Pipeline] ───→ [Retrieval Index / Vector Store]
         ↓
 [Agent Core & Specialized Tools] ←── [Structured Metadata DB / Store]
         ↓
 [Evidence & Provenance Layer]
         ↓
 [User Interface (Web/Dashboard)]
```

### 1. Data Layers (Planned)
- **Raw Layer**: Original immutable contract PDFs (`Data/raw/`).
- **Parsed/Processed Layer**: Clean extracted text with retained section headings, tables, and page metadata.
- **Structured Metadata Layer**: Extracted entities, obligations, dates, parties, and governing laws.
- **Retrieval Index Layer**: Semantic embeddings + lexical index supporting hybrid search and reranking.

### 2. Processing Pipeline (Planned)
- **PDF Ingestion**: Layout-preserving text extraction mapping clauses to exact page coordinates/numbers.
- **Structure-Aware Chunking**: Semantic chunking respecting clause boundaries (sections, subsections, exhibits).
- **Hybrid Retrieval**: Dense vector retrieval combined with keyword/exact-term search for legal terms and definitions.
- **Reranking**: Precision reranker to bubble up high-relevance clauses for the agent context window.

### 3. Agent & Tooling Layer (Planned)
- **Deterministic Tool Calling**: Specialized tools for structured lookups (obligations by date, party search, deadline filtering) rather than pure LLM generation.
- **Evidence Layer**: Grounded reasoning tying every generated answer or flag to specific document name, section, and page number.
- **Core Agent Actions**: Contract Q&A, amendment conflict resolution, obligation timeline compilation, and risk flagging.

### 4. Presentation Layer (Planned)
- Interactive web UI / dashboard enabling contract upload, portfolio exploration, clause-level citation previews, and obligation calendars.
