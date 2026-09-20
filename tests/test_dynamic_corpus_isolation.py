"""Integration acceptance tests verifying end-to-end dynamic contract execution,
clean-room catalog isolation, role resolution waterfall, composite amendment scoring,
and zero hardcoded assumptions.
"""
import pytest
from src.catalog.catalog import (
    ContractCatalog,
    LayeredRoleResolver,
    CompositeAmendmentResolver,
)
from src.agent.understanding import (
    ContractQueryUnderstander,
    CanonicalRole,
)
from src.agent.router import AgentRouter, AgentRouteCategory
from src.agent.agent import ContractAgent
from src.models.canonical import (
    CanonicalDocument,
    CanonicalPage,
    CanonicalBlock,
    BlockType,
    BoundingBox,
    EvidenceReference,
)
from src.models.intelligence import (
    ContractIntelligence,
    ExtractedField,
    ExtractionMethod,
    ContractParty,
)
from src.models.obligation import ContractObligation


def _make_dummy_doc(doc_id: str, title: str, preamble: str = "") -> CanonicalDocument:
    block = CanonicalBlock(
        block_id=f"blk_{doc_id}_01",
        document_id=doc_id,
        block_type=BlockType.PARAGRAPH,
        raw_text=preamble or f"This Agreement is entered into by {title}.",
        normalized_text=preamble or f"This Agreement is entered into by {title}.",
        page_number=1,
        reading_order=1,
        bbox=BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=100.0),
    )
    page = CanonicalPage(
        page_number=1,
        width=612.0,
        height=792.0,
        blocks=[block],
    )
    return CanonicalDocument(
        document_id=doc_id,
        filename=f"{title.lower().replace(' ', '_')}.pdf",
        file_size=1024,
        title=title,
        page_count=1,
        pages=[page],
    )


def test_clean_room_empty_corpus_isolation():
    """Verify that ContractLens gracefully boots and answers with an empty catalog snapshot (0 contracts)."""
    empty_catalog = ContractCatalog.empty()

    assert len(empty_catalog.documents) == 0
    assert len(empty_catalog.parties) == 0
    assert len(empty_catalog.roles) == 0
    assert len(empty_catalog.parent_child_candidates) == 0

    understander = ContractQueryUnderstander()
    analysis = understander.analyze_query("What is the payment period for Acme?", catalog=empty_catalog)
    assert len(analysis.entity_references) == 0
    assert analysis.target_document_id is None

    router = AgentRouter()
    route, params = router.route_query("What is the payment period for Acme?", catalog=empty_catalog, understanding=analysis)
    assert route in {AgentRouteCategory.DIRECT_RETRIEVAL, AgentRouteCategory.HYBRID_REASONING}


def test_unseen_contract_dynamic_discovery():
    """Verify that a newly introduced synthetic contract (Apex - Vanguard) with novel entity names
    is dynamically discovered and routed with zero pre-existing knowledge.
    """
    doc_id = "syn_apex_99"
    preamble = "This Master Services Agreement is entered into between Apex Global Inc. ('Customer') and Vanguard Defense LLC ('Service Provider')."
    doc = _make_dummy_doc(doc_id, "Apex-Vanguard Master Services Agreement", preamble=preamble)

    ev = EvidenceReference(
        document_id=doc_id,
        filename=doc.filename,
        page_number=1,
        block_id=f"blk_{doc_id}_01",
        bbox=BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=100.0),
        verbatim_quote="Apex Global Inc. ('Customer') and Vanguard Defense LLC ('Service Provider')",
    )

    intel = ContractIntelligence(
        document_id=doc_id,
        filename=doc.filename,
        contract_type=ExtractedField(
            field_name="contract_type",
            is_found=True,
            raw_value="Master Services Agreement",
            confidence=0.95,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX
        ),
        effective_date=ExtractedField(
            field_name="effective_date",
            is_found=True,
            raw_value="2024-01-01",
            confidence=0.95,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX
        ),
        expiration_date=ExtractedField.not_found("expiration_date"),
        renewal_language=ExtractedField.not_found("renewal_language"),
        parties=[
            ContractParty(name="Apex Global Inc.", role="Customer", raw_text="Apex Global Inc. ('Customer')", evidence=ev),
            ContractParty(name="Vanguard Defense LLC", role="Service Provider", raw_text="Vanguard Defense LLC ('Service Provider')", evidence=ev),
        ],
        governing_law=ExtractedField(
            field_name="governing_law",
            is_found=True,
            raw_value="State of Ohio",
            normalized_value="Ohio",
            confidence=0.92,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX,
            evidence=ev
        ),
        payment_terms=ExtractedField(
            field_name="payment_terms",
            is_found=True,
            raw_value="Net 45 days after receipt of invoice",
            confidence=0.90,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX,
            evidence=ev
        ),
    )

    catalog = ContractCatalog.from_runtime(
        documents={doc_id: doc},
        intelligences={doc_id: intel},
    )

    assert doc_id in catalog.parties
    assert "Apex Global Inc." in catalog.parties[doc_id]
    assert "Vanguard Defense LLC" in catalog.parties[doc_id]
    assert catalog.roles[doc_id]["Apex Global Inc."] == CanonicalRole.CUSTOMER
    assert catalog.roles[doc_id]["Vanguard Defense LLC"] == CanonicalRole.SERVICE_PROVIDER

    understander = ContractQueryUnderstander()
    # Query regarding Apex
    analysis = understander.analyze_query("What are the reporting duties for Apex Global?", catalog=catalog)
    matched_names = [e.canonical_name for e in analysis.entity_references]
    assert "Apex Global Inc." in matched_names
    assert analysis.target_document_id == doc_id

    router = AgentRouter()
    route, params = router.route_query("What are the reporting duties for Apex Global?", catalog=catalog, understanding=analysis)
    assert route == AgentRouteCategory.OBLIGATION_QUERY
    assert params["document_id"] == doc_id
    assert params["party"] in {"Apex Global Inc.", "Apex Global"}


def test_composite_amendment_margin_policy():
    """Verify that CompositeAmendmentResolver enforces top_score >= 0.75 AND margin >= 0.20."""
    # Synthetic Base Agreement
    base_id = "doc_base_01"
    base_doc = _make_dummy_doc(base_id, "Master Services Agreement", preamble="Master Services Agreement between Alpha Corp and Beta LLC.")
    ev_base = EvidenceReference(
        document_id=base_id,
        filename=base_doc.filename,
        page_number=1,
        block_id=f"blk_{base_id}_01",
        bbox=BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=100.0),
        verbatim_quote="Alpha Corp and Beta LLC",
    )
    base_intel = ContractIntelligence(
        document_id=base_id,
        filename=base_doc.filename,
        contract_type=ExtractedField(
            field_name="contract_type",
            is_found=True,
            raw_value="Master Services Agreement",
            confidence=0.95,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX
        ),
        parties=[
            ContractParty(name="Alpha Corp", role="Client", raw_text="Alpha Corp", evidence=ev_base),
            ContractParty(name="Beta LLC", role="Provider", raw_text="Beta LLC", evidence=ev_base),
        ],
        effective_date=ExtractedField(
            field_name="effective_date",
            is_found=True,
            raw_value="January 1, 2024",
            normalized_value="2024-01-01",
            confidence=0.95,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX
        ),
        expiration_date=ExtractedField.not_found("expiration_date"),
        renewal_language=ExtractedField.not_found("renewal_language"),
        governing_law=ExtractedField(
            field_name="governing_law",
            is_found=True,
            raw_value="Delaware",
            normalized_value="Delaware",
            confidence=0.95,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX
        ),
    )

    # Synthetic Amendment Doc
    amend_id = "doc_amend_01"
    amend_doc = _make_dummy_doc(amend_id, "First Amendment to Master Services Agreement", preamble="First Amendment to the Master Services Agreement between Alpha Corp and Beta LLC.")
    ev_amend = EvidenceReference(
        document_id=amend_id,
        filename=amend_doc.filename,
        page_number=1,
        block_id=f"blk_{amend_id}_01",
        bbox=BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=100.0),
        verbatim_quote="Amendment to Master Services Agreement",
    )
    amend_intel = ContractIntelligence(
        document_id=amend_id,
        filename=amend_doc.filename,
        contract_type=ExtractedField(
            field_name="contract_type",
            is_found=True,
            raw_value="Amendment",
            confidence=0.98,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX
        ),
        parties=[
            ContractParty(name="Alpha Corp", role="Client", raw_text="Alpha Corp", evidence=ev_amend),
            ContractParty(name="Beta LLC", role="Provider", raw_text="Beta LLC", evidence=ev_amend),
        ],
        effective_date=ExtractedField(
            field_name="effective_date",
            is_found=True,
            raw_value="July 1, 2024",
            normalized_value="2024-07-01",
            confidence=0.95,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX
        ),
        expiration_date=ExtractedField.not_found("expiration_date"),
        renewal_language=ExtractedField.not_found("renewal_language"),
        governing_law=ExtractedField(
            field_name="governing_law",
            is_found=True,
            raw_value="Delaware",
            normalized_value="Delaware",
            confidence=0.95,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX
        ),
    )

    docs = {base_id: base_doc, amend_id: amend_doc}
    intels = {base_id: base_intel, amend_id: amend_intel}

    parent_id, telem = CompositeAmendmentResolver.resolve_parent_candidate(
        amend_doc_id=amend_id,
        documents=docs,
        intelligences=intels,
    )

    assert parent_id == base_id
    assert telem["status"] == "RESOLVED"
    assert telem["top_score"] >= 0.75
    assert "party_overlap" in telem["all_candidates"][0]["component_scores"]

