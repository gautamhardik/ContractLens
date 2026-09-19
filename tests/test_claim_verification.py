"""Targeted Unit Tests for Claim Verification Engine (Phase 16).

Tests:
- Test A: Simple payment term supported (Net 30 in claim and evidence).
- Test B: Wrong payment term rejected (Net 60 claim vs Net 30 evidence).
- Test C: Negation / contradiction detection (No automatic renewal vs renews).
- Test D: Modality check ('may' permissive vs 'shall' mandatory).
- Test E: Date grounding (June 1, 2005 verified).
- Test F: Insufficient evidence (Claim without evidence or empty content).
- Test G: Citation integrity (Model references invalid evidence ID like E999).
- Test H: Multi-evidence span requirement.
"""

import pytest
from src.models.canonical import BoundingBox
from src.evidence.models import EvidenceSpan
from src.rag.models import (
    GroundedClaim,
    ClaimVerificationStatus,
    VerificationResult,
)
from src.rag.verifier import ClaimVerifier


@pytest.fixture
def sample_evidence_spans():
    """Deterministic mock evidence spans."""
    e1 = EvidenceSpan(
        document_id="doc_03",
        filename="Access-E-TRADE MSA.pdf",
        page_number=3,
        block_id="blk_01",
        reading_order=0,
        raw_text="Section 6. Payment Terms. Invoices shall be paid within thirty (30) days following receipt.",
        normalized_text="Section 6. Payment Terms. Invoices shall be paid within thirty (30) days following receipt.",
        bbox=BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=150.0),
        section_number="6.0",
        section_title="Payment Terms",
    )
    e2 = EvidenceSpan(
        document_id="doc_03",
        filename="Access-E-TRADE MSA.pdf",
        page_number=1,
        block_id="blk_02",
        reading_order=1,
        raw_text="This Agreement is entered into effective June 1, 2005 by and between Access and E*TRADE.",
        normalized_text="This Agreement is entered into effective June 1, 2005 by and between Access and E*TRADE.",
        bbox=BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=90.0),
        section_number="1.0",
        section_title="Effective Date",
    )
    e3 = EvidenceSpan(
        document_id="doc_01",
        filename="AMX Supply Agreement.pdf",
        page_number=5,
        block_id="blk_03",
        reading_order=3,
        raw_text="Section 9. Term. The Agreement terminates on December 31, 2025 without automatic renewal.",
        normalized_text="Section 9. Term. The Agreement terminates on December 31, 2025 without automatic renewal.",
        bbox=BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=140.0),
        section_number="9.0",
        section_title="Term",
    )
    e4 = EvidenceSpan(
        document_id="doc_01",
        filename="AMX Supply Agreement.pdf",
        page_number=4,
        block_id="blk_04",
        reading_order=2,
        raw_text="Vendor shall submit quality inspection reports to Buyer on a monthly basis.",
        normalized_text="Vendor shall submit quality inspection reports to Buyer on a monthly basis.",
        bbox=BoundingBox(x0=50.0, y0=80.0, x1=500.0, y1=120.0),
        section_number="4.2",
        section_title="Quality Reports",
    )
    return {"E1": e1, "E2": e2, "E3": e3, "E4": e4}


def test_a_simple_payment_supported(sample_evidence_spans):
    """Test A: Verifier confirms Net 30 claim supported by E1."""
    claim = GroundedClaim(
        claim_id="c1",
        text="Invoices are payable within 30 days of receipt.",
        evidence_ids=["E1"]
    )
    res = ClaimVerifier.verify_claim(claim, sample_evidence_spans)
    assert res.is_supported is True
    assert res.status == ClaimVerificationStatus.SUPPORTED
    assert len(res.resolved_citations) == 1
    assert res.resolved_citations[0].page_number == 3


def test_b_wrong_payment_term_rejected(sample_evidence_spans):
    """Test B: Verifier detects numeric discrepancy (Net 60 asserted vs 30 in evidence)."""
    claim = GroundedClaim(
        claim_id="c2",
        text="Invoices are payable within 60 days.",
        evidence_ids=["E1"]
    )
    res = ClaimVerifier.verify_claim(claim, sample_evidence_spans)
    assert res.is_supported is False
    assert res.status == ClaimVerificationStatus.UNSUPPORTED
    assert "Numeric discrepancy" in res.reason


def test_c_negation_contradiction(sample_evidence_spans):
    """Test C: Verifier detects contradiction (asserting automatic renewal when text states 'without automatic renewal')."""
    claim = GroundedClaim(
        claim_id="c3",
        text="The agreement automatically renews after December 31, 2025.",
        evidence_ids=["E3"]
    )
    res = ClaimVerifier.verify_claim(claim, sample_evidence_spans)
    assert res.is_supported is False
    assert res.status == ClaimVerificationStatus.CONTRADICTED
    assert "Contradiction" in res.reason


def test_d_obligation_modality(sample_evidence_spans):
    """Test D: Modality check - downgrading mandatory 'shall' to permissive 'may' is flagged as PARTIALLY_SUPPORTED."""
    claim = GroundedClaim(
        claim_id="c4",
        text="Vendor may submit quality inspection reports on a monthly basis.",
        evidence_ids=["E4"]
    )
    res = ClaimVerifier.verify_claim(claim, sample_evidence_spans)
    assert res.is_supported is False
    assert res.status == ClaimVerificationStatus.PARTIALLY_SUPPORTED
    assert "Modality mismatch" in res.reason


def test_e_date_grounding(sample_evidence_spans):
    """Test E: Effective date June 1, 2005 verified."""
    claim = GroundedClaim(
        claim_id="c5",
        text="The Agreement became effective on June 1, 2005.",
        evidence_ids=["E2"]
    )
    res = ClaimVerifier.verify_claim(claim, sample_evidence_spans)
    assert res.is_supported is True
    assert res.status == ClaimVerificationStatus.SUPPORTED


def test_f_insufficient_evidence(sample_evidence_spans):
    """Test F: Claim without evidence IDs returns INSUFFICIENT_EVIDENCE."""
    claim = GroundedClaim(
        claim_id="c6",
        text="The contract has an initial 5 year term.",
        evidence_ids=[]
    )
    res = ClaimVerifier.verify_claim(claim, sample_evidence_spans)
    assert res.is_supported is False
    assert res.status == ClaimVerificationStatus.INSUFFICIENT_EVIDENCE


def test_g_invalid_citation_reference(sample_evidence_spans):
    """Test G: Referencing an unknown evidence ID fails as UNSUPPORTED."""
    claim = GroundedClaim(
        claim_id="c7",
        text="Some contractual assertion.",
        evidence_ids=["E999"]
    )
    res = ClaimVerifier.verify_claim(claim, sample_evidence_spans)
    assert res.is_supported is False
    assert res.status == ClaimVerificationStatus.UNSUPPORTED
    assert "non-existent evidence IDs" in res.reason


def test_h_multi_evidence_spans(sample_evidence_spans):
    """Test H: Claim citing multiple evidence spans resolves all citations."""
    claim = GroundedClaim(
        claim_id="c8",
        text="Effective June 1, 2005, invoices must be paid within 30 days.",
        evidence_ids=["E1", "E2"]
    )
    res = ClaimVerifier.verify_claim(claim, sample_evidence_spans)
    assert res.is_supported is True
    assert len(res.resolved_citations) == 2
    doc_ids = {c.document_id for c in res.resolved_citations}
    assert "doc_03" in doc_ids
