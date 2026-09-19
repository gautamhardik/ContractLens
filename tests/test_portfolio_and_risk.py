"""Unit and Integration Tests for Portfolio and Risk Engines (Phases 23-26)."""

import pytest
from src.models.canonical import CanonicalDocument, CanonicalPage, CanonicalBlock, BlockType, BoundingBox, EvidenceReference
from src.models.intelligence import ContractIntelligence, ExtractedField, ExtractionMethod, ContractParty, PaymentTerms
from src.models.obligation import ContractObligation, TemporalConstraint, TemporalType, ObligationStatus, LifecycleEvent, LifecycleEventType
from src.portfolio.aggregator import PortfolioAggregator
from src.risk.detector import RiskDetector, RiskSeverity


@pytest.fixture
def sample_portfolio_data():
    bbox = BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=100.0, page_number=1)
    b1 = CanonicalBlock(
        block_id="b1",
        document_id="doc_01",
        page_number=1,
        reading_order=0,
        block_type=BlockType.PARAGRAPH,
        bbox=bbox,
        raw_text="AMX Supply Agreement with Best Circuit Boards.",
        normalized_text="AMX Supply Agreement with Best Circuit Boards.",
    )
    p1 = CanonicalPage(page_number=1, width=612.0, height=792.0, blocks=[b1])
    doc1 = CanonicalDocument(document_id="doc_01", filename="AMX-Best Circuit Boards Supply Agreement.pdf", file_size=1024, page_count=1, pages=[p1])

    b2 = CanonicalBlock(
        block_id="b2",
        document_id="doc_03",
        page_number=1,
        reading_order=0,
        block_type=BlockType.PARAGRAPH,
        bbox=bbox,
        raw_text="Access Master Services Agreement with E*TRADE.",
        normalized_text="Access Master Services Agreement with E*TRADE.",
    )
    p2 = CanonicalPage(page_number=1, width=612.0, height=792.0, blocks=[b2])
    doc2 = CanonicalDocument(document_id="doc_03", filename="Access-E-TRADE MSA.pdf", file_size=2048, page_count=12, pages=[p2])

    ev1 = EvidenceReference(document_id="doc_01", filename="AMX-Best Circuit Boards Supply Agreement.pdf", page_number=1, block_id="b1", bbox=bbox)
    ev2 = EvidenceReference(document_id="doc_03", filename="Access-E-TRADE MSA.pdf", page_number=1, block_id="b2", bbox=bbox)

    intel1 = ContractIntelligence(
        document_id="doc_01",
        filename="AMX-Best Circuit Boards Supply Agreement.pdf",
        contract_type=ExtractedField(field_name="contract_type", raw_value="Supply Agreement", normalized_value="Supply Agreement", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX),
        effective_date=ExtractedField(field_name="effective_date", raw_value="August 28, 2006", normalized_value="2006-08-28", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev1),
        expiration_date=ExtractedField(field_name="expiration_date", raw_value="August 28, 2009", normalized_value="2009-08-28", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev1),
        renewal_language=ExtractedField(field_name="renewal_language", raw_value="Automatically renews for successive 1-year terms with 60 days notice", normalized_value="successive 1-year terms", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev1),
        governing_law=ExtractedField(field_name="governing_law", raw_value="State of Texas", normalized_value="State of Texas", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev1),
        payment_terms=ExtractedField(field_name="payment_terms", raw_value="Net 30", normalized_value=PaymentTerms(payment_type="Net 30", payment_days=30, raw_text="Net 30", evidence=ev1), extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev1),
        parties=[
            ContractParty(name="AMX, LLC", raw_text="AMX, LLC", evidence=ev1),
            ContractParty(name="BEST CIRCUIT BOARDS, INC.", raw_text="BEST CIRCUIT BOARDS, INC", evidence=ev1)
        ]
    )

    intel2 = ContractIntelligence(
        document_id="doc_03",
        filename="Access-E-TRADE MSA.pdf",
        contract_type=ExtractedField(field_name="contract_type", raw_value="Master Services Agreement", normalized_value="Master Services Agreement", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX),
        effective_date=ExtractedField(field_name="effective_date", raw_value="June 1, 2005", normalized_value="2005-06-01", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev2),
        expiration_date=ExtractedField(field_name="expiration_date", raw_value="September 30, 2010", normalized_value="2010-09-30", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev2),
        renewal_language=ExtractedField.not_found("renewal_language"),
        governing_law=ExtractedField(field_name="governing_law", raw_value="State of Delaware", normalized_value="State of Delaware", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev2),
        payment_terms=ExtractedField(field_name="payment_terms", raw_value="Net 60", normalized_value=PaymentTerms(payment_type="Net 60", payment_days=60, raw_text="Net 60", evidence=ev2), extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev2),
        parties=[
            ContractParty(name="Access Worldwide Communications, Inc", raw_text="Access Worldwide Communications, Inc", evidence=ev2),
            ContractParty(name="E*TRADE Financial Corporation", raw_text="E*TRADE Financial Corporation", evidence=ev2)
        ]
    )

    ob1 = ContractObligation(
        obligation_id="ob_01",
        actor="BEST CIRCUIT BOARDS, INC.",
        action="deliver circuit boards per purchase order specifications",
        temporal=TemporalConstraint(temporal_type=TemporalType.ONGOING, raw_expression="ongoing"),
        status=ObligationStatus.UNKNOWN,
        source_clause="Section 2.1",
        evidence=ev1,
    )

    ob2 = ContractObligation(
        obligation_id="ob_02",
        actor="Access Worldwide Communications, Inc",
        action="provide marketing services",
        temporal=TemporalConstraint(temporal_type=TemporalType.RELATIVE_OFFSET, raw_expression="within 30 days"),
        status=ObligationStatus.UNKNOWN,
        source_clause="Section 4",
        evidence=ev2,
    )

    evt1 = LifecycleEvent(
        event_id="evt_01",
        event_type=LifecycleEventType.EFFECTIVE_DATE,
        title="Contract Effective Date",
        description="Agreement takes effect",
        date_or_trigger="2006-08-28",
        is_fixed_date=True,
        evidence=ev1,
    )

    evt2 = LifecycleEvent(
        event_id="evt_02",
        event_type=LifecycleEventType.EXPIRATION,
        title="Contract Expiration",
        description="Agreement expires",
        date_or_trigger="2009-08-28",
        is_fixed_date=True,
        evidence=ev1,
    )

    evt3 = LifecycleEvent(
        event_id="evt_03",
        event_type=LifecycleEventType.NOTICE_DEADLINE,
        title="Renewal Notice Deadline",
        description="60 days prior to expiration",
        date_or_trigger="2009-06-29",
        is_fixed_date=True,
        evidence=ev1,
    )

    evt4 = LifecycleEvent(
        event_id="evt_04",
        event_type=LifecycleEventType.EFFECTIVE_DATE,
        title="Contract Effective Date",
        description="Agreement takes effect",
        date_or_trigger="2005-06-01",
        is_fixed_date=True,
        evidence=ev2,
    )

    return [doc1, doc2], {"doc_01": intel1, "doc_03": intel2}, [ob1, ob2], [evt1, evt2, evt3, evt4]


def test_portfolio_aggregator(sample_portfolio_data):
    """Test portfolio-level KPIs and distributions."""
    docs, intel_docs, obs, evs = sample_portfolio_data
    overview = PortfolioAggregator.aggregate(docs, intel_docs, obs, evs)

    assert overview.total_contracts == 2
    assert overview.total_pages == 13
    assert overview.total_obligations == 2
    assert overview.total_events == 4

    assert overview.governing_laws.get("State of Texas") == 1
    assert overview.governing_laws.get("State of Delaware") == 1

    assert overview.payment_terms.get("Net 30") == 1
    assert overview.payment_terms.get("Net 60") == 1

    assert len(overview.counterparties) >= 4
    party_names = [c.name for c in overview.counterparties]
    assert "AMX, LLC" in party_names
    assert "E*TRADE Financial Corporation" in party_names


def test_risk_detector_auto_renewal_trap(sample_portfolio_data):
    """Test proactive detection of auto-renewal lock-in mechanism."""
    docs, intel_docs, obs, evs = sample_portfolio_data
    doc1 = docs[0]
    intel1 = intel_docs["doc_01"]

    report = RiskDetector.analyze_contract(doc1, intel1, [obs[0]])
    assert report.total_signals >= 1
    types = [s.risk_type for s in report.signals]
    assert "AUTO_RENEWAL_TRAP" in types

    auto_sig = [s for s in report.signals if s.risk_type == "AUTO_RENEWAL_TRAP"][0]
    assert auto_sig.severity == RiskSeverity.HIGH
    assert "successive" in auto_sig.description
    assert report.risk_score > 0.0


def test_risk_detector_clean_contract(sample_portfolio_data):
    """Test contract without renewal trap has lower risk score."""
    docs, intel_docs, obs, evs = sample_portfolio_data
    doc2 = docs[1]
    intel2 = intel_docs["doc_03"]

    report = RiskDetector.analyze_contract(doc2, intel2, [obs[1]])
    # Should not flag AUTO_RENEWAL_TRAP
    types = [s.risk_type for s in report.signals]
    assert "AUTO_RENEWAL_TRAP" not in types
