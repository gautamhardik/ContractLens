# Architecture & Engineering Decisions

Log of accepted decisions and intentionally undecided choices. Update this document as architectural directions are finalized.

---

## Accepted Decisions

### Decision: Problem Statement Selection
- **Status**: LOCKED
- **Selection**: PS4 — ContractLens: Business Contract Review & Obligation Tracking Agent.
- **Context**: Hackathon 2026 selected scope.

### Decision: Raw Contract Corpus Sourcing
- **Status**: Accepted
- **Selection**: 18 real-world, publicly available commercial contract and amendment PDFs placed in `Data/raw/`.
- **Context**: Real-world documents ensure rigorous testing of real-world layout, boilerplate clauses, amendments, and definitions.

### Decision: Raw Data Immutability
- **Status**: Accepted
- **Selection**: Files inside `Data/raw/` are strictly read-only and immutable.
- **Context**: Ensures evaluation consistency and prevents corrupting original source material.

### Decision: Context & Agent Memory Architecture
- **Status**: Accepted
- **Selection**: 3-layer hierarchy (Always-on Rules in `.agents/rules/`, Compact Project Memory in `docs/agent-context/`, Task Skills in `.agents/skills/`).
- **Context**: Minimizes repetitive repository audits and token spend across agent turns.

---

## Intentionally Undecided Decisions (Pending Future Milestones)

- **Backend Language / Framework**: Undecided (e.g., Python FastAPI / Flask / Node.js).
- **PDF Parsing Engine**: Undecided (e.g., PyMuPDF, pdfplumber, LlamaParse, unstructured).
- **Chunking Strategy**: Undecided (e.g., section-aware semantic splitting vs. token-based sliding window).
- **Embedding Model**: Undecided (e.g., text-embedding-3-small, Vertex AI embeddings, open-source models).
- **Vector Database / Index**: Undecided (e.g., ChromaDB, Qdrant, FAISS, pgvector).
- **Reranker Model**: Undecided (e.g., Cohere rerank, FlashRank, Cross-Encoder).
- **LLM / Model Provider**: Undecided (e.g., Gemini 1.5 Pro/Flash, OpenAI, Claude).
- **Frontend Framework**: Undecided (e.g., React + Vite, Next.js, Streamlit).
- **Database for Structured Metadata**: Undecided (e.g., SQLite, PostgreSQL).
