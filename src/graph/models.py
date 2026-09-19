"""Knowledge Graph Data Models for ContractLens (Phase 17).

Defines strongly-typed representations for:
- NodeType: Formal entity types (CONTRACT, PARTY, OBLIGATION, EVENT, PAYMENT_TERM, AMENDMENT, JURISDICTION).
- EdgeType: Directional relationships connecting nodes.
- GraphNode: Typed entity preserving authoritative EvidenceReferences.
- GraphEdge: Relationship connecting two nodes with properties and evidence.
- GraphFact: Atomic predicate-value assertion with mandatory provenance.
- ContractKnowledgeGraph: Complete container holding nodes, edges, facts, and provenance index.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from src.models.canonical import EvidenceReference, BoundingBox


class NodeType(str, Enum):
    """Explicit domain entity types in ContractLens."""
    CONTRACT = "CONTRACT"
    PARTY = "PARTY"
    OBLIGATION = "OBLIGATION"
    EVENT = "EVENT"
    PAYMENT_TERM = "PAYMENT_TERM"
    AMENDMENT = "AMENDMENT"
    JURISDICTION = "JURISDICTION"


class EdgeType(str, Enum):
    """Directional relationships connecting entities in the Contract Knowledge Graph."""
    # Contract relationships
    HAS_PARTY = "HAS_PARTY"
    HAS_OBLIGATION = "HAS_OBLIGATION"
    HAS_EVENT = "HAS_EVENT"
    HAS_PAYMENT_TERM = "HAS_PAYMENT_TERM"
    HAS_AMENDMENT = "HAS_AMENDMENT"
    GOVERNED_BY = "GOVERNED_BY"

    # Party relationships
    COUNTERPARTY_TO = "COUNTERPARTY_TO"
    OWNS_OBLIGATION = "OWNS_OBLIGATION"
    BENEFICIARY_OF = "BENEFICIARY_OF"

    # Amendment relationships
    AMENDS = "AMENDS"
    MODIFIES_SECTION = "MODIFIES_SECTION"
    SUPERSEDES = "SUPERSEDES"

    # Obligation relationships
    ASSIGNED_TO = "ASSIGNED_TO"
    OWED_TO = "OWED_TO"
    HAS_DEADLINE = "HAS_DEADLINE"


class GraphNode(BaseModel):
    """Typed domain entity in the knowledge graph with mandatory provenance."""
    node_id: str
    node_type: NodeType
    label: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    evidence: Optional[EvidenceReference] = None
    document_id: Optional[str] = None


class GraphEdge(BaseModel):
    """Directed, typed relationship between two nodes with evidence provenance."""
    edge_id: str
    source_node_id: str
    relationship: EdgeType
    target_node_id: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    evidence: Optional[EvidenceReference] = None
    document_id: Optional[str] = None


class GraphFact(BaseModel):
    """Atomic contractual fact assertion with mandatory evidence provenance."""
    fact_id: str
    subject_id: str
    predicate: str
    value: Any
    raw_text: Optional[str] = None
    evidence: EvidenceReference
    document_id: str
    confidence: float = 1.0
    is_amended: bool = False
    amendment_id: Optional[str] = None


class KnowledgeGraph(BaseModel):
    """In-memory Knowledge Graph representing verified contract facts and relationships."""
    nodes: Dict[str, GraphNode] = Field(default_factory=dict)
    edges: Dict[str, GraphEdge] = Field(default_factory=dict)
    facts: List[GraphFact] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges[edge.edge_id] = edge

    def add_fact(self, fact: GraphFact) -> None:
        self.facts.append(fact)
