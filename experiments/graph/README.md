# Phase 17: Contract Knowledge Graph & Cross-Contract Reasoning

## Overview
Phase 17 implements a typed, provenance-aware Contract Knowledge Graph over all 18 contracts (696 pages) in the ContractLens corpus.

## Architecture
```
Canonical Documents (18 contracts / 696 pages)
       ↓
Contract Intelligence + Obligations + Lifecycle Events
       ↓
KnowledgeGraphBuilder (Deterministic Entity & Relationship Mapping)
       ↓
GraphValidator (100% Provenance & Zero Orphan Invariants)
       ↓
GraphIndex (In-memory Inverted Multi-Attribute Index)
       ↓
ContractGraphQueryEngine (Sub-millisecond Cross-Contract Queries)
       ↓
Evidence Bridge (QueryResultItem with Exact EvidenceReference)
```

## Measured Graph Statistics
- **Total Nodes**: 3287
  - `CONTRACT`: 15
  - `JURISDICTION`: 9
  - `PARTY`: 29
  - `PAYMENT_TERM`: 12
  - `OBLIGATION`: 3118
  - `EVENT`: 101
  - `AMENDMENT`: 3
- **Total Edges**: 4359
  - `GOVERNED_BY`: 10
  - `HAS_PARTY`: 31
  - `COUNTERPARTY_TO`: 31
  - `HAS_PAYMENT_TERM`: 12
  - `HAS_OBLIGATION`: 3118
  - `HAS_EVENT`: 101
  - `OWNS_OBLIGATION`: 1054
  - `AMENDS`: 1
  - `HAS_AMENDMENT`: 1
- **Total Contractual Facts**: 61
- **Facts with Valid Provenance**: 61 (100.0%)
- **Unsupported Graph Fact Rate**: 0.0%
- **Orphan Edge Rate**: 0.0% (0 orphan edges)
- **Graph Construction Latency**: 488.28 ms
- **Graph Validation Latency**: 22.88 ms

## Cross-Contract Reasoning Benchmark
- **Queries Evaluated**: 10
- **Reasoning Accuracy**: 100.0%
- **Average Query Latency**: 0.037 ms

### Benchmark Query Results
| Category | Query Type | Description | Passed | Latency (ms) |
| :--- | :--- | :--- | :--- | :--- |
| GRAPH_DIRECT | `get_contract` | Fetch Access-E*TRADE contract node | PASSED | 0.007 |
| GRAPH_RELATIONSHIP | `get_parties_for_contract` | Fetch contracting parties for AMX Best Circuit Boards | PASSED | 0.047 |
| CROSS_CONTRACT | `get_contracts_for_party` | Which contracts involve E*TRADE? | PASSED | 0.141 |
| CROSS_CONTRACT | `get_contracts_with_payment_term` | Which contracts have 30-day payment terms? | PASSED | 0.032 |
| TEMPORAL | `get_contracts_with_renewal` | Which contracts contain renewal provisions? | PASSED | 0.010 |
| TEMPORAL | `get_contracts_with_termination_notice` | Which contracts specify termination notice periods? | PASSED | 0.018 |
| AMENDMENT | `get_amendments_for_contract` | Which amendments modify the Access-E*TRADE MSA? | PASSED | 0.007 |
| AMENDMENT | `amendment_precedence` | Verify Access-E*TRADE amendment modifies price, term, payment without deleting parent | PASSED | 0.005 |
| EVIDENCE_PROVENANCE | `provenance_audit` | Verify query results retain valid Document, Page, and BBox references | PASSED | 0.016 |
| NON_GRAPH / UNANSWERABLE_SAFETY | `safe_unanswerable` | Verify querying non-existent party returns empty results safely | PASSED | 0.088 |

