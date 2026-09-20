# Architecture

## Current Implementation Status
**Complete Production Implementation (Phases 1–46).**
ContractLens is fully realized with:
- PyMuPDF canonical reconstruction (`src/ingestion/reconstructor.py`) preserving bounding boxes (`[x0, y0, x1, y1]`).
- Deterministic extraction and obligation/event engine (`src/ingestion/`, `src/temporal/`).
- Dynamic runtime `ContractCatalog` snapshot (`src/catalog/catalog.py`) with zero hardcoded entities or document IDs.
- Hybrid RRF retrieval (`src/retrieval/`) and selective FlashRank reranking.
- Knowledge graph and deterministic query engine (`src/graph/`).
- Bounded agent with deterministic router and LLM tool planner (`src/agent/`).
- Grounded RAG answer generator with citation verification and anti-scratchpad guardrails (`src/rag/`).
- Dynamic PDF upload pipeline (`POST /api/contracts/upload`) and SSE query streaming (`POST /api/query/stream`).
- Modular React + Vite frontend workspace (`frontend/`) with spatial evidence shard, amendment diff viewer, and portfolio analytics.

---

## Planned Architecture (Master Target)

ContractLens is designed as an agentic contract intelligence and operations platform. It converts static commercial agreements into a structured contract brain backed by a canonical document model, hybrid retrieval, deterministic tool routing, and verifiable evidence.

```
                         CONTRACT FILES (Data/raw/)
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  DOCUMENT INGESTION │
                         └──────────┬──────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │ CANONICAL DOCUMENT MODEL  │
                      └─────────────┬─────────────┘
                                    │
             ┌──────────────────────┼──────────────────────┐
             ▼                      ▼                      ▼
      STRUCTURED DATA        KNOWLEDGE GRAPH          RAG INDEX
   (Parties/Terms/Dates)    (Amends/DependsOn)     ┌───────┼───────┐
             │                      │              ▼       ▼       ▼
             │                      │            Dense   BM25  Reranker
             │                      │              │       │       │
             └──────────────────────┼──────────────┴───────┴───────┘
                                    │
                                    ▼
                             EVIDENCE ENGINE
                       (Page, Section, Text Box)
                                    │
                                    ▼
                            AGENT ORCHESTRATOR
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
           SEARCH              OBLIGATIONS             COMPARE
        (Contracts)             (Events)              (Versions)
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                            VERIFICATION LAYER
                        (Citation & Grounding)
                                    │
                                    ▼
                             GROUNDED ANSWER
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
           SUMMARY               TIMELINE              CHANGES
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    │
                                    ▼
                            PREMIUM FRONTEND
                  (Portfolio, Workspace, Evidence Drawer)
```

---

## Core Intelligence Systems (Planned)

1. **Contract Understanding**: Extraction of parties, effective dates, governing laws, payment terms, liability caps, and termination rights.
2. **Obligation Intelligence**: Structured mapping of "Who must do what, when, and under what condition" with exact clause provenance.
3. **Temporal & Event Engine**: Deterministic parsing of relative/event-triggered deadlines (e.g., "within 30 days after invoice received").
4. **Version Intelligence**: Section alignment and change classification (ADDED, MODIFIED, REMOVED, UNCHANGED) between base agreements and amendments.
5. **Portfolio Intelligence**: Cross-contract aggregations (e.g., upcoming renewals, notice windows, supplier commitments).
6. **Agentic Investigation**: Multi-step tool planner navigating structured data, vector search, and comparison routines with citation verification.
