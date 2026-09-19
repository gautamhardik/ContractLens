"""In-Memory Knowledge Graph Index for ContractLens (Phase 17).

Provides high-efficiency O(1) indexed lookups:
- By NodeType (contracts, parties, obligations, events, jurisdictions, payment terms).
- Outgoing and incoming edges by node_id and EdgeType.
- Facts indexed by subject_id and predicate.
- Reverse index from EvidenceReference (doc_id, page_number) to entities and facts.
"""

from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

from src.graph.models import (
    KnowledgeGraph,
    GraphNode,
    GraphEdge,
    GraphFact,
    NodeType,
    EdgeType,
)


class GraphIndex:
    """In-memory indexing layer enabling sub-millisecond graph traversals and queries."""

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

        # Indexes
        self.nodes_by_type: Dict[NodeType, List[GraphNode]] = defaultdict(list)
        self.out_edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self.in_edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self.edges_by_type: Dict[EdgeType, List[GraphEdge]] = defaultdict(list)
        
        self.facts_by_subject: Dict[str, List[GraphFact]] = defaultdict(list)
        self.facts_by_predicate: Dict[str, List[GraphFact]] = defaultdict(list)
        
        self.party_to_contracts: Dict[str, Set[str]] = defaultdict(set)
        self.contract_to_parties: Dict[str, Set[str]] = defaultdict(set)

        self._build_indexes()

    def _build_indexes(self) -> None:
        """Populate inverted indices."""
        for node in self.graph.nodes.values():
            self.nodes_by_type[node.node_type].append(node)

        for edge in self.graph.edges.values():
            self.out_edges[edge.source_node_id].append(edge)
            self.in_edges[edge.target_node_id].append(edge)
            self.edges_by_type[edge.relationship].append(edge)

            # Contract <-> Party bidirectional tracking
            if edge.relationship == EdgeType.HAS_PARTY:
                self.contract_to_parties[edge.source_node_id].add(edge.target_node_id)
                self.party_to_contracts[edge.target_node_id].add(edge.source_node_id)
            elif edge.relationship == EdgeType.COUNTERPARTY_TO:
                self.party_to_contracts[edge.source_node_id].add(edge.target_node_id)
                self.contract_to_parties[edge.target_node_id].add(edge.source_node_id)

        for fact in self.graph.facts:
            self.facts_by_subject[fact.subject_id].append(fact)
            self.facts_by_predicate[fact.predicate].append(fact)

    def get_nodes(self, node_type: NodeType) -> List[GraphNode]:
        return self.nodes_by_type.get(node_type, [])

    def get_outgoing_neighbors(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphNode]:
        edges = self.out_edges.get(node_id, [])
        if edge_type:
            edges = [e for e in edges if e.relationship == edge_type]
        return [self.graph.nodes[e.target_node_id] for e in edges if e.target_node_id in self.graph.nodes]

    def get_incoming_neighbors(self, node_id: str, edge_type: Optional[EdgeType] = None) -> List[GraphNode]:
        edges = self.in_edges.get(node_id, [])
        if edge_type:
            edges = [e for e in edges if e.relationship == edge_type]
        return [self.graph.nodes[e.source_node_id] for e in edges if e.source_node_id in self.graph.nodes]
