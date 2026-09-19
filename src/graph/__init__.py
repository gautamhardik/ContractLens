"""Knowledge Graph & Cross-Contract Reasoning Module for ContractLens (Phase 17).

Provides:
- KnowledgeGraph data structures (NodeType, EdgeType, GraphNode, GraphEdge, GraphFact, KnowledgeGraph).
- KnowledgeGraphBuilder for deterministic extraction-to-graph translation.
- GraphValidator for graph relational integrity and 100% provenance verification.
- GraphIndex for high-efficiency in-memory multi-attribute queries.
- ContractGraphQueryEngine for cross-contract factual reasoning with source provenance.
"""

from src.graph.models import (
    NodeType,
    EdgeType,
    GraphNode,
    GraphEdge,
    GraphFact,
    KnowledgeGraph,
)
from src.graph.validator import GraphValidator, GraphValidationReport
from src.graph.builder import KnowledgeGraphBuilder
from src.graph.index import GraphIndex
from src.graph.query import (
    ContractGraphQueryEngine,
    QueryResultItem,
    CrossContractQueryResult,
)

__all__ = [
    "NodeType",
    "EdgeType",
    "GraphNode",
    "GraphEdge",
    "GraphFact",
    "KnowledgeGraph",
    "GraphValidator",
    "GraphValidationReport",
    "KnowledgeGraphBuilder",
    "GraphIndex",
    "ContractGraphQueryEngine",
    "QueryResultItem",
    "CrossContractQueryResult",
]
