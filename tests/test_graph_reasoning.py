"""Tests for Cross-Contract Reasoning, Query Engine, and Real Corpus Cases (Phase 17).

Covers:
TEST 13: Cross-contract party query
TEST 14: Cross-contract payment query
TEST 15: Amendment query
TEST 16: Evidence returned with graph result
TEST 17: Conflicting parent/amendment facts are not silently merged
TEST 18: No fabricated dates
Real Corpus Cases: Access-E*TRADE amendment pair
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
from src.graph.query import ContractGraphQueryEngine


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
    renewal_text: str = None,
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

    if renewal_text:
        ren_field = ExtractedField[str](
            field_name="renewal_language",
            raw_value=renewal_text,
            normalized_value=renewal_text,
            extraction_method=ExtractionMethod.DETERMINISTIC_HEURISTIC,
            evidence=ev,
            is_found=True,
        )
    else:
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


def test_13_cross_contract_party_query():
    doc1 = _make_dummy_doc("doc_01", "Vendor_MSA_1.pdf")
    doc2 = _make_dummy_doc("doc_02", "Vendor_MSA_2.pdf")
    doc3 = _make_dummy_doc("doc_03", "Other_Contract.pdf")

    ev1 = _make_dummy_evidence("doc_01", "Vendor_MSA_1.pdf")
    ev2 = _make_dummy_evidence("doc_02", "Vendor_MSA_2.pdf")
    ev3 = _make_dummy_evidence("doc_03", "Other_Contract.pdf")

    intel1 = _make_dummy_intel(
        "doc_01", "Vendor_MSA_1.pdf",
        parties=[ContractParty(name="Global Vendor Inc.", role="Provider", raw_text="Global Vendor Inc.", evidence=ev1)]
    )
    intel2 = _make_dummy_intel(
        "doc_02", "Vendor_MSA_2.pdf",
        parties=[ContractParty(name="Global Vendor Corp", role="Consultant", raw_text="Global Vendor Corp", evidence=ev2)]
    )
    intel3 = _make_dummy_intel(
        "doc_03", "Other_Contract.pdf",
        parties=[ContractParty(name="Independent LLC", role="Partner", raw_text="Independent LLC", evidence=ev3)]
    )

    graph = KnowledgeGraphBuilder.build_graph([doc1, doc2, doc3], [intel1, intel2, intel3])
    engine = ContractGraphQueryEngine(graph)

    res = engine.get_contracts_for_party("Global Vendor")
    assert len(res) == 2
    matched_doc_ids = {item.contract_id for item in res}
    assert matched_doc_ids == {"doc_01", "doc_02"}


def test_14_cross_contract_payment_query():
    doc1 = _make_dummy_doc("doc_01", "Contract_Net30.pdf")
    doc2 = _make_dummy_doc("doc_02", "Contract_Net60.pdf")
    doc3 = _make_dummy_doc("doc_03", "Contract_AlsoNet30.pdf")

    ev1 = _make_dummy_evidence("doc_01", "Contract_Net30.pdf")
    ev2 = _make_dummy_evidence("doc_02", "Contract_Net60.pdf")
    ev3 = _make_dummy_evidence("doc_03", "Contract_AlsoNet30.pdf")

    intel1 = _make_dummy_intel(
        "doc_01", "Contract_Net30.pdf",
        payment_terms=PaymentTerms(payment_type="Net 30", payment_days=30, raw_text="Net 30 days", evidence=ev1)
    )
    intel2 = _make_dummy_intel(
        "doc_02", "Contract_Net60.pdf",
        payment_terms=PaymentTerms(payment_type="Net 60", payment_days=60, raw_text="Net 60 days", evidence=ev2)
    )
    intel3 = _make_dummy_intel(
        "doc_03", "Contract_AlsoNet30.pdf",
        payment_terms=PaymentTerms(payment_type="Net 30", payment_days=30, raw_text="Net 30 calendar days", evidence=ev3)
    )

    graph = KnowledgeGraphBuilder.build_graph([doc1, doc2, doc3], [intel1, intel2, intel3])
    engine = ContractGraphQueryEngine(graph)

    res = engine.get_contracts_with_payment_term("30")
    assert len(res) == 2
    matched_docs = {item.contract_id for item in res}
    assert matched_docs == {"doc_01", "doc_03"}


def test_15_amendment_query():
    parent_doc = _make_dummy_doc("doc_03", "Access-E-TRADE-MSA.pdf")
    amend_doc = _make_dummy_doc("doc_02", "Access-E-TRADE-Amendment.pdf")

    parent_intel = _make_dummy_intel("doc_03", "Access-E-TRADE-MSA.pdf")
    amend_intel = _make_dummy_intel("doc_02", "Access-E-TRADE-Amendment.pdf", contract_type="Amendment")

    graph = KnowledgeGraphBuilder.build_graph([parent_doc, amend_doc], [parent_intel, amend_intel])
    engine = ContractGraphQueryEngine(graph)

    # Query amendments for parent
    res = engine.get_amendments_for_contract("doc_03")
    assert len(res) == 1
    assert res[0].matched_value == "Access-E-TRADE-Amendment.pdf"

    # Query parent amended by child
    amend_edges = [e for e in graph.edges.values() if e.relationship == EdgeType.AMENDS]
    assert len(amend_edges) == 1
    assert amend_edges[0].source_node_id == "contract_doc_02"
    assert amend_edges[0].target_node_id == "contract_doc_03"


def test_16_evidence_returned_with_graph_result():
    doc = _make_dummy_doc("doc_01", "SLA.pdf")
    ev = _make_dummy_evidence("doc_01", "SLA.pdf")
    intel = _make_dummy_intel(
        "doc_01", "SLA.pdf",
        payment_terms=PaymentTerms(payment_type="Net 45", payment_days=45, raw_text="Payment within 45 days", evidence=ev)
    )

    graph = KnowledgeGraphBuilder.build_graph([doc], [intel])
    engine = ContractGraphQueryEngine(graph)

    res = engine.get_contracts_with_payment_term("45")
    assert len(res) == 1
    item = res[0]
    assert item.evidence is not None
    assert item.evidence.document_id == "doc_01"
    assert item.evidence.page_number == 1
    assert item.evidence.bbox.x0 == 50.0
    assert item.evidence.bbox.y1 == 100.0


def test_17_conflicting_parent_amendment_facts_not_silently_merged():
    parent_doc = _make_dummy_doc("doc_03", "Access-E-TRADE-MSA.pdf")
    amend_doc = _make_dummy_doc("doc_02", "Access-E-TRADE-Amendment.pdf")

    ev_parent = _make_dummy_evidence("doc_03", "Access-E-TRADE-MSA.pdf")
    parent_intel = _make_dummy_intel(
        "doc_03",
        "Access-E-TRADE-MSA.pdf",
        payment_terms=PaymentTerms(payment_type="Net 30", payment_days=30, raw_text="Net 30 days", evidence=ev_parent),
    )

    ev_amend = _make_dummy_evidence("doc_02", "Access-E-TRADE-Amendment.pdf")
    amend_intel = _make_dummy_intel(
        "doc_02",
        "Access-E-TRADE-Amendment.pdf",
        contract_type="Amendment",
        amendment_facts=[
            AmendmentFact(
                action="DELETE_AND_REPLACE",
                target_section="Section 6",
                summary="Section 6 Payment is hereby deleted and replaced in its entirety.",
                raw_text="Section 6 Payment is hereby deleted and replaced in its entirety.",
                evidence=ev_amend,
            )
        ],
    )

    graph = KnowledgeGraphBuilder.build_graph([parent_doc, amend_doc], [parent_intel, amend_intel])

    parent_payment_node = graph.nodes.get("pt_doc_03")
    assert parent_payment_node is not None
    assert parent_payment_node.properties["payment_days"] == 30

    amendment_edges = [e for e in graph.edges.values() if e.relationship == EdgeType.AMENDS]
    assert len(amendment_edges) == 1

    # Historical parent fact was not overwritten into 'DELETED' or removed
    parent_payment_facts = [f for f in graph.facts if f.subject_id == "contract_doc_03" and f.predicate == "payment_terms"]
    assert len(parent_payment_facts) == 1
    assert "Net 30" in str(parent_payment_facts[0].value)

    # Amendment modification fact is recorded under the amendment subject
    amend_mod_facts = [f for f in graph.facts if f.subject_id == "contract_doc_02" and "amendment_" in f.predicate]
    assert len(amend_mod_facts) == 1
    assert "deleted and replaced" in amend_mod_facts[0].value


def test_18_no_fabricated_dates():
    doc = _make_dummy_doc("doc_01", "Contract_Indefinite.pdf")
    intel = _make_dummy_intel("doc_01", "Contract_Indefinite.pdf")
    ev = _make_dummy_evidence("doc_01", "Contract_Indefinite.pdf")

    unresolved_event = LifecycleEvent(
        event_id="ev_indef_1",
        event_type=LifecycleEventType.TERMINATION,
        title="Termination Trigger",
        description="Subject to ongoing mutual convenience",
        date_or_trigger="Subject to ongoing mutual convenience",
        is_fixed_date=False,
        evidence=ev,
    )

    graph = KnowledgeGraphBuilder.build_graph([doc], [intel], events_by_doc={"doc_01": [unresolved_event]})
    ev_node = [n for n in graph.nodes.values() if n.node_type == NodeType.EVENT][0]

    assert ev_node.properties["is_fixed_date"] is False
    assert ev_node.properties["date_or_trigger"] == "Subject to ongoing mutual convenience"
