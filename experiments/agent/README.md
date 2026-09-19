# Phase 18 & 18.1: Controlled Contract Agent Benchmark

## Overview
Evaluates the `ContractAgent` across 16 representative contractual queries spanning all 8 routing categories, documenting the Phase 18 baseline and Phase 18.1 role-alias hardening.

## Architecture
```
User Query
    ↓
AgentRouter (Rule-first Deterministic Routing + Conversational Role Resolution)
    ↓
ToolRegistry (search_contract_evidence, query_contract_graph, get_contract_details,
              get_contract_obligations, get_contract_timeline, get_contract_amendments)
    ↓
AgentExecutor (Strict Guardrails: MAX_STEPS=6, Provenance Preservation)
    ↓
build_grounded_answer (Phase 16 Grounded RAG + Independent Claim Verification)
    ↓
AgentResponse (Grounded Answer + Citations + Full Trace)
```

## Measured Metrics Comparison

| Metric | Phase 18 Baseline | Phase 18.1 (Hardened) | Delta / Target |
| :--- | :---: | :---: | :---: |
| **Total Queries Evaluated** | 16 | 16 | 16 |
| **Routing / Selection Accuracy** | 100.0% | 100.0% | 100.0% |
| **Tool Execution Success** | 96.8% | **100.0%** | +3.2% |
| **Task Completion Rate** | 100.0% | 100.0% | 100.0% |
| **Final Answer Grounding** | 92.31% (12/13) | **100.0%** (13/13) | **+7.69%** |
| **Citation Validity** | 100.0% | 100.0% | 100.0% |
| **Unsupported Claim Rate** | 0.0% | 0.0% | 0.0% (Target: 0.0%) |
| **Unanswerable Safety** | 100.0% | 100.0% | 100.0% (Target: 100.0%) |
| **Average Tool Calls per Query** | 1.94 | 1.94 | 1.94 |
| **Average Latency** | 1.72 ms | 10.83 ms | Warm cache |

### Query Evaluation Results
| ID | Category | Query | Route | Steps | Status | Latency (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| agent_q01 | DIRECT_GRAPH | Which contracts involve E*TRADE? | `DIRECT_GRAPH` | 2 | `supported` | 19.15 |
| agent_q02 | DIRECT_GRAPH | Which contracts have Net 30 payment terms? | `DIRECT_GRAPH` | 2 | `supported` | 1.33 |
| agent_q03 | DIRECT_GRAPH | Which agreements have renewal provisions? | `DIRECT_GRAPH` | 2 | `supported` | 3.37 |
| agent_q04 | DIRECT_RETRIEVAL | What does Section 6 say about invoice payment in the Access agreement? | `DIRECT_RETRIEVAL` | 2 | `supported` | 91.96 |
| agent_q05 | DIRECT_RETRIEVAL | What is the confidentiality obligation in the agreement? | `DIRECT_RETRIEVAL` | 2 | `supported` | 30.91 |
| agent_q06 | CONTRACT_DETAILS | What are the payment terms in the Access agreement? | `CONTRACT_DETAILS` | 2 | `supported` | 0.37 |
| agent_q07 | CONTRACT_DETAILS | What is the governing law of the Access agreement? | `CONTRACT_DETAILS` | 2 | `supported` | 0.61 |
| agent_q08 | OBLIGATION_QUERY | What obligations does the vendor have under the AMX agreement? | `OBLIGATION_QUERY` | 2 | `supported` | 1.35 |
| agent_q09 | OBLIGATION_QUERY | What are the reporting obligations in the Access agreement? | `OBLIGATION_QUERY` | 2 | `supported` | 0.90 |
| agent_q10 | TIMELINE_QUERY | When does the Access agreement expire? | `TIMELINE_QUERY` | 2 | `supported` | 2.36 |
| agent_q11 | TIMELINE_QUERY | What should I review first among the upcoming contract events? | `TIMELINE_QUERY` | 2 | `supported` | 2.94 |
| agent_q12 | AMENDMENT_QUERY | What changed in the Access-E*TRADE amendment? | `AMENDMENT_QUERY` | 3 | `supported` | 17.38 |
| agent_q13 | HYBRID_REASONING | Which contracts involving E*TRADE have Net 30 payment terms? | `HYBRID_REASONING` | 3 | `supported` | 0.31 |
| agent_q14 | UNANSWERABLE | What is the CEO personal salary mentioned in the agreement? | `UNANSWERABLE` | 1 | `insufficient_evidence` | 0.05 |
| agent_q15 | UNANSWERABLE | Tell me something not contained in the contracts. | `UNANSWERABLE` | 1 | `insufficient_evidence` | 0.04 |
| agent_q16 | UNANSWERABLE | What is the stock ticker of the vendor not mentioned in the contracts? | `UNANSWERABLE` | 1 | `insufficient_evidence` | 0.04 |

