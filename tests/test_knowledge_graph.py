"""Tests for Contract Knowledge Graph Models, Validation, and Building (Phase 17).

Covers:
TEST 1: Contract node creation
TEST 2: Party node creation
TEST 3: Contract-party relationship
TEST 4: Obligation mapping
TEST 5: Payment-term mapping
TEST 6: Lifecycle-event mapping
TEST 7: Amendment -> parent contract relationship
TEST 8: Provenance preservation
TEST 9: Invalid provenance rejection
TEST 10: Duplicate node handling
TEST 11: Orphan edge detection
TEST 12: Unresolved temporal constraint preservation
"""

import pytest
from src.models.canonical import (
    CanonicalDocument,
    CanonicalPage,
    CanonicalBlock,
    BoundingBox,
    EvidenceReference,
    BlockType,
)
from src.models.intelligence import (
    ContractIntelligence,
    ContractParty,
    PaymentTerms,
    TerminationNotice,
    AmendmentFact,
    ExtractedField,
    ExtractionMethod,
)
from src.models.obligation import (
    ContractObligation,
    LifecycleEvent,
    LifecycleEventType,
    TemporalConstraint,
    TemporalType,
    ObligationStatus,
)
from src.graph.models import (
    NodeType,
    EdgeType,
    GraphNode,
    GraphEdge,
    GraphFact,
    KnowledgeGraph,
)
from src.graph.builder import KnowledgeGraphBuilder
from src.graph.validator import GraphValidator


def _make_dummy_doc(doc_id: str, filename: str) -> CanonicalDocument:
    bbox = BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=100.0, page_number=1)
    block = CanonicalBlock(
        block_id="b1",
        document_id=doc_id,
        page_number=1,
        reading_order=0,
        block_type=BlockType.PARAGRAPH,
        bbox=bbox,
        raw_text=f"Agreement for {filename}",
        normalized_text=f"Agreement for {filename}",
    )
    page = CanonicalPage(page_number=1, width=612.0, height=792.0, blocks=[block])
    return CanonicalDocument(
        document_id=doc_id,
        filename=filename,
        file_size=1024,
        page_count=1,
        pages=[page],
    )


def _make_dummy_evidence(doc_id: str, filename: str, page: int = 1, block_id: str = "b1") -> EvidenceReference:
    return EvidenceReference(
        document_id=doc_id,
        filename=filename,
        page_number=page,
        block_id=block_id,
        bbox=BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=100.0, page_number=page),
    )


def _make_dummy_intel(
    doc_id: str,
    filename: str,
    contract_type: str = "Agreement",
    governing_law: str = None,
    parties: list = None,
    payment_terms: PaymentTerms = None,
    termination_notice: TerminationNotice = None,
    amendment_facts: list = None,
) -> ContractIntelligence:
    ev = _make_dummy_evidence(doc_id, filename)
    ct_field = ExtractedField[str](
        field_name="contract_type",
        raw_value=contract_type,
        normalized_value=contract_type,
        extraction_method=ExtractionMethod.DETERMINISTIC_HEURISTIC,
        evidence=ev,
        is_found=True,
    )
    ed_field = ExtractedField[str].not_found("effective_date")
    exp_field = ExtractedField[str].not_found("expiration_date")
    ren_field = ExtractedField[str].not_found("renewal_language")

    if governing_law:
        gov_field = ExtractedField[str](
            field_name="governing_law",
            raw_value=governing_law,
            normalized_value=governing_law,
            extraction_method=ExtractionMethod.DETERMINISTIC_HEURISTIC,
            evidence=ev,
            is_found=True,
        )
    else:
        gov_field = ExtractedField[str].not_found("governing_law")

    pt_field = None
    if payment_terms:
        pt_field = ExtractedField[PaymentTerms](
            field_name="payment_terms",
            raw_value=payment_terms.raw_text,
            normalized_value=payment_terms,
            extraction_method=ExtractionMethod.DETERMINISTIC_HEURISTIC,
            evidence=payment_terms.evidence,
            is_found=True,
        )

    tn_field = None
    if termination_notice:
        tn_field = ExtractedField[TerminationNotice](
            field_name="termination_notice",
            raw_value=termination_notice.raw_text,
            normalized_value=termination_notice,
            extraction_method=ExtractionMethod.DETERMINISTIC_HEURISTIC,
            evidence=termination_notice.evidence,
            is_found=True,
        )

    return ContractIntelligence(
        document_id=doc_id,
        filename=filename,
        contract_type=ct_field,
        effective_date=ed_field,
        expiration_date=exp_field,
        renewal_language=ren_field,
        governing_law=gov_field,
        parties=parties or [],
        payment_terms=pt_field,
        termination_notice=tn_field,
        amendment_facts=amendment_facts or [],
    )


def test_1_contract_node_creation():
    doc = _make_dummy_doc("doc_01", "Master_Services_Agreement.pdf")
    intel = _make_dummy_intel(
        "doc_01",
        "Master_Services_Agreement.pdf",
        contract_type="MSA",
        governing_law="Delaware",
    )
    graph = KnowledgeGraphBuilder.build_graph([doc], [intel])

    node = graph.nodes.get("contract_doc_01")
    assert node is not None
    assert node.node_type == NodeType.CONTRACT
    assert node.label == "Master_Services_Agreement.pdf"
    assert node.properties["contract_type"] == "MSA"


def test_2_party_node_creation():
    doc = _make_dummy_doc("doc_01", "Vendor_Agreement.pdf")
    ev = _make_dummy_evidence("doc_01", "Vendor_Agreement.pdf")
    parties = [
        ContractParty(name="Acme Corporation, Inc.", role="Vendor", raw_text="Acme Corporation, Inc.", evidence=ev),
        ContractParty(name="Beta Systems LLC", role="Client", raw_text="Beta Systems LLC", evidence=ev),
    ]
    intel = _make_dummy_intel("doc_01", "Vendor_Agreement.pdf", parties=parties)
    graph = KnowledgeGraphBuilder.build_graph([doc], [intel])

    party_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.PARTY]
    assert len(party_nodes) == 2
    party_labels = {n.label for n in party_nodes}
    assert "Acme Corporation, Inc." in party_labels
    assert "Beta Systems LLC" in party_labels


def test_3_contract_party_relationship():
    doc = _make_dummy_doc("doc_01", "Vendor_Agreement.pdf")
    ev = _make_dummy_evidence("doc_01", "Vendor_Agreement.pdf")
    parties = [
        ContractParty(name="Acme Corporation, Inc.", role="Vendor", raw_text="Acme Corporation, Inc.", evidence=ev),
    ]
    intel = _make_dummy_intel("doc_01", "Vendor_Agreement.pdf", parties=parties)
    graph = KnowledgeGraphBuilder.build_graph([doc], [intel])

    has_party_edges = [e for e in graph.edges.values() if e.relationship == EdgeType.HAS_PARTY]
    assert len(has_party_edges) == 1
    edge = has_party_edges[0]
    assert edge.source_node_id == "contract_doc_01"
    assert edge.target_node_id.startswith("party_")
    assert edge.properties["role"] == "Vendor"


def test_4_obligation_mapping():
    doc = _make_dummy_doc("doc_01", "SLA.pdf")
    intel = _make_dummy_intel("doc_01", "SLA.pdf")
    ev = _make_dummy_evidence("doc_01", "SLA.pdf", 1, "b1")
    temporal = TemporalConstraint(
        temporal_type=TemporalType.RECURRING,
        raw_expression="monthly",
        is_resolved=True,
    )
    ob = ContractObligation(
        obligation_id="ob_1",
        actor="Provider",
        actor_role="Provider",
        action="provide monthly uptime reports",
        object_or_scope="uptime reports",
        temporal=temporal,
        status=ObligationStatus.UNKNOWN,
        source_clause="Section 4",
        evidence=ev,
    )
    graph = KnowledgeGraphBuilder.build_graph([doc], [intel], obligations_by_doc={"doc_01": [ob]})

    ob_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.OBLIGATION]
    assert len(ob_nodes) == 1
    node = ob_nodes[0]
    assert "provide monthly" in node.properties["action"]
    assert node.properties["temporal_type"] == "RECURRING"
    assert node.evidence is not None


def test_5_payment_term_mapping():
    doc = _make_dummy_doc("doc_01", "MSA.pdf")
    ev = _make_dummy_evidence("doc_01", "MSA.pdf")
    pt = PaymentTerms(
        payment_type="Net 30",
        payment_days=30,
        raw_text="Payment shall be made within 30 days of invoice.",
        evidence=ev,
    )
    intel = _make_dummy_intel("doc_01", "MSA.pdf", payment_terms=pt)
    graph = KnowledgeGraphBuilder.build_graph([doc], [intel])

    payment_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.PAYMENT_TERM]
    assert len(payment_nodes) == 1
    p_node = payment_nodes[0]
    assert p_node.properties["payment_days"] == 30

    p_edges = [e for e in graph.edges.values() if e.relationship == EdgeType.HAS_PAYMENT_TERM]
    assert len(p_edges) == 1


def test_6_lifecycle_event_mapping():
    doc = _make_dummy_doc("doc_01", "MSA.pdf")
    intel = _make_dummy_intel("doc_01", "MSA.pdf")
    ev = _make_dummy_evidence("doc_01", "MSA.pdf")
    event = LifecycleEvent(
        event_id="ev_1",
        event_type=LifecycleEventType.EXPIRATION,
        title="Contract Initial Expiration",
        description="Agreement term expires on 2026-12-31.",
        date_or_trigger="2026-12-31",
        is_fixed_date=True,
        evidence=ev,
    )
    graph = KnowledgeGraphBuilder.build_graph([doc], [intel], events_by_doc={"doc_01": [event]})

    event_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.EVENT]
    assert len(event_nodes) == 1
    ev_node = event_nodes[0]
    assert ev_node.properties["event_type"] == "expiration"
    assert ev_node.properties["date_or_trigger"] == "2026-12-31"


def test_7_amendment_to_parent_relationship():
    parent_doc = _make_dummy_doc("doc_03", "Access-E-TRADE-MSA.pdf")
    parent_intel = _make_dummy_intel("doc_03", "Access-E-TRADE-MSA.pdf", contract_type="Master Services Agreement")

    amend_doc = _make_dummy_doc("doc_02", "Access-E-TRADE-Amendment.pdf")
    ev = _make_dummy_evidence("doc_02", "Access-E-TRADE-Amendment.pdf")
    amend_intel = _make_dummy_intel(
        "doc_02",
        "Access-E-TRADE-Amendment.pdf",
        contract_type="Amendment",
        amendment_facts=[
            AmendmentFact(
                action="DELETE_AND_REPLACE",
                target_section="Section 4",
                summary="Replaces fee structure with quarterly tiered billing.",
                raw_text="Section 4 is deleted and replaced.",
                evidence=ev,
            )
        ]
    )

    graph = KnowledgeGraphBuilder.build_graph([parent_doc, amend_doc], [parent_intel, amend_intel])

    amends_edges = [e for e in graph.edges.values() if e.relationship == EdgeType.AMENDS]
    assert len(amends_edges) == 1
    assert amends_edges[0].source_node_id == "contract_doc_02"
    assert amends_edges[0].target_node_id == "contract_doc_03"

    has_amend_edges = [e for e in graph.edges.values() if e.relationship == EdgeType.HAS_AMENDMENT]
    assert len(has_amend_edges) == 1
    assert has_amend_edges[0].source_node_id == "contract_doc_03"
    assert has_amend_edges[0].target_node_id == "contract_doc_02"


def test_8_provenance_preservation():
    doc = _make_dummy_doc("doc_01", "Contract_A.pdf")
    intel = _make_dummy_intel("doc_01", "Contract_A.pdf", governing_law="California")
    graph = KnowledgeGraphBuilder.build_graph([doc], [intel])

    facts = [f for f in graph.facts if f.predicate == "governing_law"]
    assert len(facts) == 1
    fact = facts[0]
    assert fact.evidence is not None
    assert fact.evidence.document_id == "doc_01"
    assert fact.evidence.page_number == 1
    assert fact.evidence.bbox is not None


def test_9_invalid_provenance_rejection():
    invalid_bbox = BoundingBox(x0=500.0, y0=500.0, x1=50.0, y1=50.0)  # inverted x0 > x1
    invalid_ev = EvidenceReference(
        document_id="doc_01",
        filename="Contract.pdf",
        page_number=1,
        block_id="b1",
        bbox=invalid_bbox,
    )

    graph = KnowledgeGraph()
    graph.add_node(GraphNode(
        node_id="contract_doc_01",
        node_type=NodeType.CONTRACT,
        label="Contract.pdf",
        evidence=invalid_ev,
        document_id="doc_01",
    ))
    graph.add_fact(GraphFact(
        fact_id="fact_1",
        subject_id="contract_doc_01",
        predicate="test_pred",
        value="test_val",
        evidence=invalid_ev,
        document_id="doc_01",
    ))

    report = GraphValidator.validate(graph)
    assert not report.is_valid
    assert report.invalid_bboxes_count > 0


def test_10_duplicate_node_handling():
    doc1 = _make_dummy_doc("doc_01", "Contract_1.pdf")
    doc2 = _make_dummy_doc("doc_02", "Contract_2.pdf")
    ev1 = _make_dummy_evidence("doc_01", "Contract_1.pdf")
    ev2 = _make_dummy_evidence("doc_02", "Contract_2.pdf")

    intel1 = _make_dummy_intel(
        "doc_01", "Contract_1.pdf",
        parties=[ContractParty(name="Alpha Corp", role="Vendor", raw_text="Alpha Corp", evidence=ev1)]
    )
    intel2 = _make_dummy_intel(
        "doc_02", "Contract_2.pdf",
        parties=[ContractParty(name="Alpha Corp, Inc.", role="Client", raw_text="Alpha Corp, Inc.", evidence=ev2)]
    )

    graph = KnowledgeGraphBuilder.build_graph([doc1, doc2], [intel1, intel2])

    party_nodes = [n for n in graph.nodes.values() if n.node_type == NodeType.PARTY]
    assert len(party_nodes) == 1

    has_party_edges = [e for e in graph.edges.values() if e.relationship == EdgeType.HAS_PARTY]
    assert len(has_party_edges) == 2


def test_11_orphan_edge_detection():
    graph = KnowledgeGraph()
    graph.add_node(GraphNode(
        node_id="contract_doc_01",
        node_type=NodeType.CONTRACT,
        label="Contract.pdf",
        evidence=_make_dummy_evidence("doc_01", "Contract.pdf"),
    ))

    graph.add_edge(GraphEdge(
        edge_id="edge_orphan",
        source_node_id="contract_doc_01",
        relationship=EdgeType.HAS_PARTY,
        target_node_id="party_nonexistent",
    ))

    report = GraphValidator.validate(graph)
    assert not report.is_valid
    assert report.orphan_edges_count == 1
    assert "Orphan edge" in report.errors[0]


def test_12_unresolved_temporal_constraint_preservation():
    doc = _make_dummy_doc("doc_01", "MSA.pdf")
    intel = _make_dummy_intel("doc_01", "MSA.pdf")
    ev = _make_dummy_evidence("doc_01", "MSA.pdf")
    unresolved_event = LifecycleEvent(
        event_id="ev_rel_1",
        event_type=LifecycleEventType.TERMINATION,
        title="Termination Notice Trigger",
        description="30 days prior to end of initial term",
        date_or_trigger="30 days prior to end of initial term",
        is_fixed_date=False,  # Unresolved calendar date preserved!
        evidence=ev,
    )
    graph = KnowledgeGraphBuilder.build_graph([doc], [intel], events_by_doc={"doc_01": [unresolved_event]})

    ev_node = [n for n in graph.nodes.values() if n.node_type == NodeType.EVENT][0]
    assert ev_node.properties["is_fixed_date"] is False
    assert ev_node.properties["date_or_trigger"] == "30 days prior to end of initial term"
