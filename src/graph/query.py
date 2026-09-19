"""Deterministic Cross-Contract Query Engine for ContractLens (Phase 17).

Provides structured query APIs:
- get_contract(contract_id)
- get_contracts_for_party(party_name_or_id)
- get_parties_for_contract(contract_id)
- get_obligations(contract_id)
- get_obligations_for_party(party_name_or_id)
- get_contracts_with_payment_term(payment_type_or_days)
- get_contracts_with_renewal()
- get_contracts_with_termination_notice(min_days)
- get_amendments_for_contract(contract_id)
- get_contracts_amended_by(amendment_id)
- get_cross_contract_party_network(party_name_or_id)

CRITICAL INVARIANT: Every query result preserves source EvidenceReferences for auditability.
"""

from typing import List, Dict, Any, Optional, Set, Union
from pydantic import BaseModel, Field

from src.models.canonical import EvidenceReference
from src.graph.models import (
    KnowledgeGraph,
    GraphNode,
    GraphEdge,
    GraphFact,
    NodeType,
    EdgeType,
)
from src.graph.index import GraphIndex
from src.graph.builder import KnowledgeGraphBuilder


class QueryResultItem(BaseModel):
    """Structured query response item with mandatory evidence provenance."""
    entity_id: str
    entity_label: str
    entity_type: str
    contract_id: str
    contract_filename: str
    matched_property: str
    matched_value: Any
    evidence: EvidenceReference


class CrossContractQueryResult(BaseModel):
    """Aggregate cross-contract query response containing matched items and provenance."""
    query_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    total_matches: int = 0
    results: List[QueryResultItem] = Field(default_factory=list)
    latency_ms: float = 0.0


class ContractGraphQueryEngine:
    """High-performance deterministic query engine operating over the indexed KnowledgeGraph."""

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.index = GraphIndex(graph)

    def get_contract(self, doc_id: str) -> Optional[GraphNode]:
        """Fetch contract node by doc_id (e.g. 'doc_03' or 'contract_doc_03')."""
        nid = doc_id if doc_id.startswith("contract_") else f"contract_{doc_id}"
        return self.graph.nodes.get(nid)

    def get_contracts_for_party(self, party_name: str) -> List[QueryResultItem]:
        """Find all contracts where a given party is a contracting counterparty."""
        norm_query = KnowledgeGraphBuilder.normalize_party_name(party_name)
        results: List[QueryResultItem] = []

        # Find matching party nodes
        matching_party_nodes = [
            n for n in self.index.get_nodes(NodeType.PARTY)
            if norm_query in n.node_id or norm_query in KnowledgeGraphBuilder.normalize_party_name(n.label)
        ]

        for p_node in matching_party_nodes:
            contract_ids = self.index.party_to_contracts.get(p_node.node_id, set())
            for cid in contract_ids:
                c_node = self.graph.nodes.get(cid)
                if c_node:
                    results.append(QueryResultItem(
                        entity_id=p_node.node_id,
                        entity_label=p_node.label,
                        entity_type="PARTY",
                        contract_id=c_node.properties.get("document_id", cid),
                        contract_filename=c_node.properties.get("filename", c_node.label),
                        matched_property="party",
                        matched_value=p_node.label,
                        evidence=p_node.evidence or c_node.evidence,
                    ))

        return results

    def get_parties_for_contract(self, doc_id: str) -> List[QueryResultItem]:
        """Return all parties identified for a specific contract."""
        cid = doc_id if doc_id.startswith("contract_") else f"contract_{doc_id}"
        c_node = self.graph.nodes.get(cid)
        if not c_node:
            return []

        results: List[QueryResultItem] = []
        party_nodes = self.index.get_outgoing_neighbors(cid, edge_type=EdgeType.HAS_PARTY)

        for p in party_nodes:
            results.append(QueryResultItem(
                entity_id=p.node_id,
                entity_label=p.label,
                entity_type="PARTY",
                contract_id=c_node.properties.get("document_id", cid),
                contract_filename=c_node.properties.get("filename", c_node.label),
                matched_property="role",
                matched_value=p.properties.get("role", "Party"),
                evidence=p.evidence or c_node.evidence,
            ))
        return results

    def get_contracts_with_payment_term(self, term_pattern: str) -> List[QueryResultItem]:
        """Find contracts with specific payment terms (e.g. 'Net 30', '30', 'Net')."""
        pattern = term_pattern.lower().strip()
        results: List[QueryResultItem] = []

        payment_facts = self.index.facts_by_predicate.get("payment_terms", [])
        for f in payment_facts:
            val_str = str(f.value).lower()
            raw_str = (f.raw_text or "").lower()
            if pattern in val_str or pattern in raw_str:
                c_node = self.graph.nodes.get(f.subject_id)
                if c_node:
                    results.append(QueryResultItem(
                        entity_id=f.fact_id,
                        entity_label=f"Payment Terms: {f.value}",
                        entity_type="PAYMENT_TERM",
                        contract_id=f.document_id,
                        contract_filename=c_node.properties.get("filename", c_node.label),
                        matched_property="payment_terms",
                        matched_value=f.value,
                        evidence=f.evidence,
                    ))

        return results

    def get_contracts_with_renewal(self) -> List[QueryResultItem]:
        """Find all contracts that contain auto-renewal or renewal language."""
        results: List[QueryResultItem] = []
        renewal_facts = self.index.facts_by_predicate.get("auto_renewal", [])
        for f in renewal_facts:
            if f.value is True:
                c_node = self.graph.nodes.get(f.subject_id)
                if c_node:
                    results.append(QueryResultItem(
                        entity_id=f.fact_id,
                        entity_label="Automatic Renewal Clause",
                        entity_type="EVENT",
                        contract_id=f.document_id,
                        contract_filename=c_node.properties.get("filename", c_node.label),
                        matched_property="auto_renewal",
                        matched_value=f.raw_text or "True",
                        evidence=f.evidence,
                    ))
        return results

    def get_contracts_with_termination_notice(self, notice_days: Optional[int] = None) -> List[QueryResultItem]:
        """Find contracts specifying termination notice periods."""
        results: List[QueryResultItem] = []
        notice_facts = self.index.facts_by_predicate.get("termination_notice_days", [])
        for f in notice_facts:
            val = f.value
            if notice_days is None or (isinstance(val, int) and val == notice_days):
                c_node = self.graph.nodes.get(f.subject_id)
                if c_node:
                    results.append(QueryResultItem(
                        entity_id=f.fact_id,
                        entity_label=f"Termination Notice: {val} days",
                        entity_type="EVENT",
                        contract_id=f.document_id,
                        contract_filename=c_node.properties.get("filename", c_node.label),
                        matched_property="termination_notice_days",
                        matched_value=f.value,
                        evidence=f.evidence,
                    ))
        return results

    def get_amendments_for_contract(self, doc_id: str) -> List[QueryResultItem]:
        """Find all amendments that modify a specific parent contract."""
        cid = doc_id if doc_id.startswith("contract_") else f"contract_{doc_id}"
        c_node = self.graph.nodes.get(cid)
        if not c_node:
            return []

        results: List[QueryResultItem] = []
        # Find incoming edges of type AMENDS
        incoming_amends = [e for e in self.index.in_edges.get(cid, []) if e.relationship == EdgeType.AMENDS]
        for edge in incoming_amends:
            amend_node = self.graph.nodes.get(edge.source_node_id)
            if amend_node:
                results.append(QueryResultItem(
                    entity_id=amend_node.node_id,
                    entity_label=amend_node.label,
                    entity_type="AMENDMENT",
                    contract_id=c_node.properties.get("document_id", cid),
                    contract_filename=c_node.properties.get("filename", c_node.label),
                    matched_property="amended_by",
                    matched_value=amend_node.properties.get("filename", amend_node.label),
                    evidence=edge.evidence or amend_node.evidence,
                ))

        return results

    def get_obligations_for_party(self, party_name: str) -> List[QueryResultItem]:
        """Retrieve all obligations owned by or assigned to a party."""
        norm_party = KnowledgeGraphBuilder.normalize_party_name(party_name)
        results: List[QueryResultItem] = []

        party_nodes = [
            n for n in self.index.get_nodes(NodeType.PARTY)
            if norm_party in n.node_id or norm_party in KnowledgeGraphBuilder.normalize_party_name(n.label)
        ]

        for p in party_nodes:
            ob_nodes = self.index.get_outgoing_neighbors(p.node_id, edge_type=EdgeType.OWNS_OBLIGATION)
            for ob in ob_nodes:
                doc_id = ob.document_id or "unknown"
                c_node = self.graph.nodes.get(f"contract_{doc_id}")
                results.append(QueryResultItem(
                    entity_id=ob.node_id,
                    entity_label=ob.label,
                    entity_type="OBLIGATION",
                    contract_id=doc_id,
                    contract_filename=c_node.properties.get("filename", doc_id) if c_node else doc_id,
                    matched_property="action",
                    matched_value=ob.properties.get("action", ob.label),
                    evidence=ob.evidence,
                ))

        return results
