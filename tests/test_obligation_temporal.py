"""Focused Unit Tests for Contract Obligations, Temporal Engine & Lifecycle Events (Phase 7–9).

Validates:
1. Obligation Schema & Strongly Typed Fields
2. 7 Explicit Temporal Types (Fixed, Relative Offset, Event Relative, Recurring, Conditional, Ongoing, Unspecified)
3. Deterministic Offset & Anchor Normalization
4. Date Calculation with Anchor vs. Unresolved Anchors (No Fabrication)
5. Recurrence Modeling without premature infinite instantiation
6. Actor Resolution & 'unresolved' fallback
7. Lifecycle Event Generation with Provenance
8. Real Document Ingestion: Access-E*TRADE MSA, Amendment, and Foxconn MSA
9. Failure Cases: Ambiguous actor, no deadline, missing anchors, redacted notices
"""

import pytest
from pathlib import Path

from src.models.canonical import BoundingBox, EvidenceReference, BlockType
from src.models.obligation import (
    TemporalType,
    ObligationStatus,
    RecurrenceFrequency,
    RecurrenceRule,
    TemporalConstraint,
    ContractObligation,
    LifecycleEventType,
    LifecycleEvent,
)
from src.temporal.engine import TemporalEngine
from src.temporal.lifecycle import LifecycleEventEngine
from src.ingestion.reconstructor import StructuralReconstructor
from src.ingestion.extractor import ContractIntelligenceExtractor
from src.ingestion.obligation_extractor import ObligationExtractor


import os
import re

RAW_DIR = r"c:\Users\hiten\Downloads\ContractLens\Data\raw"


def get_raw_path(needle: str) -> str:
    """Find file in Data/raw by alphanumeric substring match."""
    needle_clean = re.sub(r'[^a-zA-Z0-9]', '', needle).lower()
    for f in os.listdir(RAW_DIR):
        f_clean = re.sub(r'[^a-zA-Z0-9]', '', f).lower()
        if needle_clean in f_clean:
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(f"File matching '{needle}' not found in {RAW_DIR}")


def test_obligation_schema_instantiation():
    """Verify strongly-typed obligation instantiation with evidence."""
    ev = EvidenceReference(
        document_id="doc_test",
        filename="test.pdf",
        page_number=1,
        block_id="b_001",
        bbox=BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=150.0),
        section_title="Section 6 Payment"
    )
    temporal = TemporalConstraint(
        temporal_type=TemporalType.RELATIVE_OFFSET,
        raw_expression="within thirty (30) days of receipt",
        offset_days=30,
        anchor_event="invoice_received",
        is_resolved=False
    )
    ob = ContractObligation(
        obligation_id="obl_test_001",
        actor="Customer",
        actor_role="Customer",
        counterparty="Vendor",
        action="shall pay all undisputed invoices",
        object_or_scope="undisputed fees",
        temporal=temporal,
        status=ObligationStatus.UNKNOWN,
        source_clause="Section 6 Payment",
        evidence=ev
    )

    assert ob.obligation_id == "obl_test_001"
    assert ob.actor == "Customer"
    assert ob.temporal.temporal_type == TemporalType.RELATIVE_OFFSET
    assert ob.temporal.offset_days == 30
    assert ob.temporal.is_resolved is False
    assert ob.status == ObligationStatus.UNKNOWN  # No fabricated completion!
    assert ob.evidence.page_number == 1


def test_temporal_engine_fixed_date():
    """Verify FIXED_DATE parsing and date resolution."""
    raw = "This agreement expires on June 30, 2027."
    tc = TemporalEngine.parse_temporal_expression(raw)
    assert tc.temporal_type == TemporalType.FIXED_DATE
    assert tc.calculated_date == "2027-06-30"
    assert tc.is_resolved is True


def test_temporal_engine_relative_offset():
    """Verify RELATIVE_OFFSET parsing and anchor preservation."""
    raw = "Payment is due within thirty (30) days after receipt of invoice."
    tc = TemporalEngine.parse_temporal_expression(raw)
    assert tc.temporal_type == TemporalType.RELATIVE_OFFSET
    assert tc.offset_days == 30
    assert tc.anchor_event == "invoice_received"
    assert tc.is_resolved is False
    assert tc.calculated_date is None

    # Calculate with known anchor date
    resolved = TemporalEngine.calculate_deadline(tc, "2026-10-01")
    assert resolved.is_resolved is True
    assert resolved.calculated_date == "2026-10-31"

    # Verify without anchor date, it remains unresolved
    unresolved = TemporalEngine.calculate_deadline(tc, None)
    assert unresolved.is_resolved is False
    assert unresolved.calculated_date is None


def test_temporal_engine_event_relative():
    """Verify EVENT_RELATIVE parsing for breaches/disputes."""
    raw = "Notify the other party within 10 days after discovering a breach."
    tc = TemporalEngine.parse_temporal_expression(raw)
    assert tc.temporal_type == TemporalType.EVENT_RELATIVE
    assert tc.offset_days == 10
    assert "breach" in tc.anchor_event
    assert tc.is_resolved is False


def test_temporal_engine_recurring_obligation():
    """Verify RECURRING obligation without infinite date generation."""
    raw = "Vendor shall provide a monthly report detailing system uptime."
    tc = TemporalEngine.parse_temporal_expression(raw)
    assert tc.temporal_type == TemporalType.RECURRING
    assert tc.recurrence is not None
    assert tc.recurrence.frequency == RecurrenceFrequency.MONTHLY
    assert tc.recurrence.interval == 1
    assert tc.is_resolved is False


def test_temporal_engine_conditional_obligation():
    """Verify CONDITIONAL obligation with trigger condition extraction."""
    raw = "If a force majeure event occurs, party shall notify the other within 15 days of such occurrence."
    tc = TemporalEngine.parse_temporal_expression(raw)
    assert tc.temporal_type == TemporalType.CONDITIONAL
    assert "force majeure" in tc.condition.lower()
    assert tc.offset_days == 15
    assert tc.is_resolved is False


def test_temporal_engine_ongoing_covenant():
    """Verify ONGOING covenant (e.g. insurance, confidentiality)."""
    raw = "Supplier shall maintain comprehensive general liability insurance throughout the term."
    tc = TemporalEngine.parse_temporal_expression(raw)
    assert tc.temporal_type == TemporalType.ONGOING
    assert tc.anchor_event == "contract_term"


def test_temporal_engine_unspecified():
    """Verify UNSPECIFIED when no timing cues exist."""
    raw = "Customer agrees to provide reasonable cooperation."
    tc = TemporalEngine.parse_temporal_expression(raw)
    assert tc.temporal_type == TemporalType.UNSPECIFIED
    assert tc.is_resolved is False


def test_actor_resolution_unresolved_no_guessing():
    """Verify actor resolution sets 'unresolved' rather than hallucinating."""
    extractor = ObligationExtractor()
    # Sentence with no identifiable actor
    sentence = "It is agreed that strict confidentiality shall be maintained."
    actor, role, cp = extractor._resolve_actors(sentence, [])
    assert actor == "unresolved"
    assert role is None


def test_access_etrade_msa_obligations():
    """End-to-end obligation extraction on Access-E*TRADE MSA."""
    pdf_path = get_raw_path("Access-E-TRADE MSA")
    doc = StructuralReconstructor().reconstruct_document(pdf_path, "doc_03")
    intel = ContractIntelligenceExtractor().extract(doc)

    extractor = ObligationExtractor()
    obligations = extractor.extract_obligations(doc, intel)

    assert len(obligations) > 0
    # Every obligation must have valid evidence
    for ob in obligations:
        assert ob.evidence is not None
        assert ob.evidence.document_id == doc.document_id
        assert ob.evidence.page_number >= 1
        assert ob.evidence.bbox.x1 > ob.evidence.bbox.x0
        assert ob.status == ObligationStatus.UNKNOWN

    # Lifecycle events
    lifecycle_events = LifecycleEventEngine.generate_lifecycle_events(doc, intel, obligations)
    assert len(lifecycle_events) >= 3
    event_types = [e.event_type for e in lifecycle_events]
    assert LifecycleEventType.EFFECTIVE_DATE in event_types
    assert LifecycleEventType.PAYMENT_DEADLINE in event_types


def test_access_etrade_amendment_obligations():
    """End-to-end obligation and lifecycle extraction on Access-E*TRADE Amendment."""
    pdf_path = get_raw_path("Access-E-TRADE Amendment")
    doc = StructuralReconstructor().reconstruct_document(pdf_path, "doc_02")
    intel = ContractIntelligenceExtractor().extract(doc)

    extractor = ObligationExtractor()
    obligations = extractor.extract_obligations(doc, intel)

    assert len(obligations) > 0
    # Check that amendment facts are converted into lifecycle events
    lifecycle_events = LifecycleEventEngine.generate_lifecycle_events(doc, intel, obligations)
    amendment_events = [e for e in lifecycle_events if e.event_type == LifecycleEventType.AMENDMENT_EFFECTIVE_DATE]
    assert len(amendment_events) >= 4  # 4 amendment clauses in Access-E*TRADE


def test_foxconn_redacted_notice_no_fabrication():
    """Verify that redacted notices (e.g. Turtle Beach-Foxconn MSA) do not invent deadlines."""
    pdf_path = get_raw_path("Turtle Beach-Foxconn MSA")
    doc = StructuralReconstructor().reconstruct_document(pdf_path, "doc_13")
    intel = ContractIntelligenceExtractor().extract(doc)

    # In doc_13, notice days were redacted [*****]
    if intel.termination_notice:
        assert intel.termination_notice.is_found is False or intel.termination_notice.normalized_value.notice_days is None

    extractor = ObligationExtractor()
    obligations = extractor.extract_obligations(doc, intel)
    assert len(obligations) > 0

    # Ensure no fabricated completion status
    for ob in obligations:
        assert ob.status == ObligationStatus.UNKNOWN
        # Check that unknown anchor events stay unresolved
        if ob.temporal.temporal_type in (TemporalType.RELATIVE_OFFSET, TemporalType.EVENT_RELATIVE):
            assert ob.temporal.is_resolved is False


def test_amx_supply_agreement_exhibit_obligations():
    """Verify obligation extraction in SOW / Exhibit context on AMX Supply Agreement."""
    pdf_path = get_raw_path("AMX")
    doc = StructuralReconstructor().reconstruct_document(pdf_path, "doc_01")
    intel = ContractIntelligenceExtractor().extract(doc)

    extractor = ObligationExtractor()
    obligations = extractor.extract_obligations(doc, intel)
    assert len(obligations) > 0

    # Verify party resolution maps to AMX or Best Circuit Boards or role
    resolved_actors = {ob.actor for ob in obligations}
    assert any("AMX" in a or "Supplier" in a or "Customer" in a or "The Parties" in a for a in resolved_actors)
