# Phase 18: Controlled Contract Agent Benchmark

## Overview
Phase 18 benchmark evaluates the `ContractAgent` across 16 queries spanning all 8 routing categories.

## Architecture
```
User Query
    ↓
AgentRouter (Rule-first Deterministic Routing)
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

## Measured Metrics
- **Total Queries Evaluated**: 16
- **Tool Selection Accuracy**: 93.8%
- **Tool Execution Success**: 100.0%
- **Task Completion Rate**: 100.0%
- **Final Answer Grounding**: 100.0%
- **Citation Validity**: 100.0%
- **Unsupported Claim Rate**: 0.0%
- **Unanswerable Safety**: 100.0%
- **Average Tool Calls per Query**: 1.94
- **Average End-to-End Latency**: 1.63 ms

### Query Evaluation Results
| ID | Category | Query | Route | Steps | Status | Latency (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| agent_q01 | DIRECT_GRAPH | Which contracts involve E*TRADE? | `DIRECT_GRAPH` | 2 | `supported` | 3.10 |
| agent_q02 | DIRECT_GRAPH | Which contracts have Net 30 payment terms? | `DIRECT_GRAPH` | 2 | `supported` | 0.68 |
| agent_q03 | DIRECT_GRAPH | Which agreements have renewal provisions? | `DIRECT_GRAPH` | 2 | `supported` | 0.61 |
| agent_q04 | DIRECT_RETRIEVAL | What does Section 6 say about invoice payment in the Access agreement? | `DIRECT_RETRIEVAL` | 2 | `supported` | 7.39 |
| agent_q05 | DIRECT_RETRIEVAL | What is the confidentiality obligation in the agreement? | `OBLIGATION_QUERY` | 2 | `supported` | 4.28 |
| agent_q06 | CONTRACT_DETAILS | What are the payment terms in the Access agreement? | `CONTRACT_DETAILS` | 2 | `supported` | 0.52 |
| agent_q07 | CONTRACT_DETAILS | What is the governing law of the Access agreement? | `CONTRACT_DETAILS` | 2 | `supported` | 0.36 |
| agent_q08 | OBLIGATION_QUERY | What obligations does the vendor have under the AMX agreement? | `OBLIGATION_QUERY` | 2 | `supported` | 0.60 |
| agent_q09 | OBLIGATION_QUERY | What are the reporting obligations in the Access agreement? | `OBLIGATION_QUERY` | 2 | `supported` | 0.87 |
| agent_q10 | TIMELINE_QUERY | When does the Access agreement expire? | `TIMELINE_QUERY` | 2 | `supported` | 0.31 |
| agent_q11 | TIMELINE_QUERY | What should I review first among the upcoming contract events? | `TIMELINE_QUERY` | 2 | `supported` | 0.47 |
| agent_q12 | AMENDMENT_QUERY | What changed in the Access-E*TRADE amendment? | `AMENDMENT_QUERY` | 3 | `supported` | 6.12 |
| agent_q13 | HYBRID_REASONING | Which contracts involving E*TRADE have Net 30 payment terms? | `HYBRID_REASONING` | 3 | `supported` | 0.44 |
| agent_q14 | UNANSWERABLE | What is the CEO personal salary mentioned in the agreement? | `UNANSWERABLE` | 1 | `insufficient_evidence` | 0.06 |
| agent_q15 | UNANSWERABLE | Tell me something not contained in the contracts. | `UNANSWERABLE` | 1 | `insufficient_evidence` | 0.04 |
| agent_q16 | UNANSWERABLE | What is the stock ticker of the vendor not mentioned in the contracts? | `UNANSWERABLE` | 1 | `insufficient_evidence` | 0.04 |

