# File Map

Quick orientation map for the ContractLens repository. Consult this map to determine where files live before navigating or modifying code.

## Root Directory
- `.agents/`: Agent configuration, operational rules, and task-specific skills.
- `docs/agent-context/`: Persistent compact memory and context protocol for agents.
- `Data/`: Project dataset storage.

## Data Layer
- `Data/raw/`: Original, immutable contract corpus (18 PDF agreements/amendments).
- `Data/corpus_manifest.json`: Corpus metadata manifest across all 18 documents.
- `Data/corpus_report.md`: Detailed structural audit of the contract corpus.

## Source Code (`src/`)
- `src/models/`: Canonical document (`canonical.py`), contract intelligence (`intelligence.py`), obligations & temporal models (`obligation.py`), and chunk models (`chunk.py`).
- `src/ingestion/`: Structural reconstructor (`reconstructor.py`), intelligence extractor (`extractor.py`), and chunking strategies (`chunker.py`).
- `src/temporal/`: Temporal constraints, recurrence rules, and date calculators (`temporal_engine.py`, `lifecycle_engine.py`).
- `src/retrieval/`: Lexical BM25 (`lexical.py`), Dense LSA (`dense.py`), Hybrid RRF (`fusion.py`), Cross-Encoder Reranker (`reranker.py`), Adaptive Retriever (`adaptive.py`), and evaluation harness (`evaluation.py`).
- `src/evidence/`: Evidence models (`models.py`), citation validator (`validator.py`), and deterministic resolver (`resolver.py`).
- `src/rag/`: Grounded RAG models (`models.py`), prompt formats (`prompts.py`), generators & providers (`generator.py`), claim verifier (`verifier.py`), and pipeline (`pipeline.py`).
- `src/graph/`: Knowledge graph models (`models.py`), schema validator (`validator.py`), graph builder (`builder.py`), inverted index (`index.py`), and query engine (`query.py`).
- `src/agent/`: Agent models (`models.py`), semantic understanding & role ontology (`understanding.py`), typed tools & registry (`tools.py`), deterministic router (`router.py`), planner (`planner.py`), bounded executor (`executor.py`), and agent facade (`agent.py`).

## Experiments (`experiments/`)
- `experiments/extraction/`: Empirical extraction benchmark and findings.
- `experiments/obligations/`: Obligation & temporal extraction evaluation.
- `experiments/evaluation/`: 40-question benchmark schema and golden dataset (`benchmark_schema.py`, `benchmark_dataset.py`).
- `experiments/chunking/`: Empirical sliding-window vs section-aware chunking benchmark.
- `experiments/retrieval/`: Empirical BM25 vs Dense vs Hybrid RRF benchmark.
- `experiments/reranking/`: Empirical cross-encoder reranking evaluation (`run_reranking_experiments.py`, `benchmark_report.md`, `failure_analysis.md`).
- `experiments/evidence/`: Empirical evidence resolution & citation integrity benchmark (`run_evidence_benchmark.py`, `README.md`, `evidence_benchmark_results.json`).
- `experiments/rag/`: Empirical Grounded RAG & claim verification benchmark (`run_rag_benchmark.py`, `README.md`, `rag_benchmark_results.json`).
- `experiments/graph/`: Empirical knowledge graph corpus benchmark (`run_graph_benchmark.py`, `README.md`, `graph_benchmark_results.json`).
- `experiments/agent/`: Empirical controlled contract agent benchmark (`run_agent_benchmark.py`, `README.md`, `agent_benchmark_results.json`).

## Tests (`tests/`)
- `tests/test_canonical_reconstruction.py`: Canonical document and reconstruction tests.
- `tests/test_intelligence_extraction.py`: Intelligence extraction tests.
- `tests/test_obligation_temporal.py`: Obligation and temporal engine tests.
- `tests/test_chunking_evaluation.py`: Benchmark dataset integrity and chunking tests.
- `tests/test_retrieval.py`: Retrieval and cross-encoder reranking tests.
- `tests/test_evidence.py`: Evidence resolution, citation validity, and bounding box tests.
- `tests/test_claim_verification.py`: Deterministic claim verification, negation, modality, and numeric tests.
- `tests/test_grounded_rag.py`: Grounded RAG pipeline, unanswerable handling, and recovery tests.
- `tests/test_knowledge_graph.py`: Knowledge graph structure, provenance invariants, and validator tests.
- `tests/test_graph_reasoning.py`: Cross-contract reasoning, party networks, payment queries, and amendment precedence tests.
- `tests/test_agent_tools.py`: Agent tool registry, argument validation, and individual tool execution tests.
- `tests/test_agent_routing.py`: Rule-first intent router and parameter extraction tests.
- `tests/test_agent_execution.py`: Multi-step agent execution, limit enforcement, trace generation, and unanswerable safety tests.
- `tests/test_role_alias_resolution.py`: Conversational role-alias resolution and party mapping tests.
- `tests/test_query_understanding.py`: Semantic query understanding, canonical role ontology, temporal cue, comparison intent, and query expansion tests.
- `tests/test_adaptive_retrieval.py`: Query-adaptive retrieval, difficulty detection, and selective FlashRank reranking tests.
