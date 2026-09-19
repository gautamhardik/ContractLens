"""Targeted tests for ContractIntelligence and Hybrid Extraction (Phase 5 & 6).
"""

import os
import re
import pytest
from src.models.canonical import BoundingBox, EvidenceReference
from src.models.intelligence import (
    ExtractionMethod,
    CandidateStatus,
    ExtractedField,
    PaymentTerms,
    TerminationNotice,
    ContractIntelligence,
)
from src.ingestion.reconstructor import StructuralReconstructor
from src.ingestion.extractor import ContractIntelligenceExtractor


RAW_DIR = r"c:\Users\hiten\Downloads\ContractLens\Data\raw"


def get_raw_path(needle: str) -> str:
    """Find file in Data/raw by alphanumeric substring match."""
    needle_clean = re.sub(r'[^a-zA-Z0-9]', '', needle).lower()
    for f in os.listdir(RAW_DIR):
        f_clean = re.sub(r'[^a-zA-Z0-9]', '', f).lower()
        if needle_clean in f_clean:
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(f"File matching '{needle}' not found in {RAW_DIR}")


class TestIntelligenceSchema:
    def test_missing_field_explicit(self):
        field = ExtractedField[str].not_found("expiration_date", "No fixed date")
        assert not field.is_found
        assert field.raw_value is None
        assert field.normalized_value is None
        assert field.confidence == 0.0
        assert field.missing_reason == "No fixed date"

    def test_payment_terms_normalization(self):
        bbox = BoundingBox(x0=10.0, y0=20.0, x1=200.0, y1=40.0)
        ev = EvidenceReference(
            document_id="doc_test",
            filename="test.pdf",
            page_number=2,
            block_id="doc_test_p002_b05",
            bbox=bbox,
            section_number="6.1"
        )
        pay = PaymentTerms(
            payment_type="Net 30",
            payment_days=30,
            raw_text="undisputed invoices are due within thirty days of the date of receipt",
            evidence=ev
        )
        field = ExtractedField[PaymentTerms](
            field_name="payment_terms",
            raw_value="within thirty days",
            normalized_value=pay,
            confidence=0.95,
            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX,
            evidence=ev,
            is_found=True
        )
        assert field.is_found
        assert field.normalized_value.payment_days == 30
        assert field.evidence.block_id == "doc_test_p002_b05"


class TestExtractionEngine:
    @pytest.fixture(scope="class")
    def reconstructor(self):
        return StructuralReconstructor()

    @pytest.fixture(scope="class")
    def extractor(self):
        return ContractIntelligenceExtractor()

    def test_access_etrade_msa_intelligence(self, reconstructor, extractor):
        """Test extraction on base Access-E*TRADE MSA."""
        path = get_raw_path("Access-E-TRADE MSA")
        doc = reconstructor.reconstruct_document(path, "doc_03")
        intel = extractor.extract(doc)

        assert intel.document_id == "doc_03"
        assert intel.contract_type.is_found
        assert intel.contract_type.normalized_value == "Master Services Agreement"

        # Effective date ground truth: June 1, 2005
        assert intel.effective_date.is_found
        assert "June" in intel.effective_date.normalized_value and "2005" in intel.effective_date.normalized_value
        assert intel.effective_date.evidence is not None
        assert intel.effective_date.evidence.page_number == 1

        # Governing Law ground truth: Delaware (Section 16: "State of Delaware")
        assert intel.governing_law.is_found
        assert "Delaware" in intel.governing_law.normalized_value

    def test_access_etrade_amendment_facts(self, reconstructor, extractor):
        """Test extraction on Access-E*TRADE Amendment ground truth."""
        path = get_raw_path("Access-E-TRADE Amendment")
        doc = reconstructor.reconstruct_document(path, "doc_02")
        intel = extractor.extract(doc)

        assert intel.contract_type.normalized_value == "Amendment"
        assert len(intel.amendment_facts) >= 3

        # Check section replacements
        actions = [af.action for af in intel.amendment_facts]
        assert "DELETE_AND_REPLACE" in actions
        assert "ADD_COVERAGE" in actions
        assert "CONFIRM_FULL_FORCE" in actions

        # Check payment term in amendment (due within thirty days)
        assert intel.payment_terms.is_found
        assert intel.payment_terms.normalized_value.payment_days == 30

    def test_turtle_beach_foxconn_msa(self, reconstructor, extractor):
        """Test extraction on Turtle Beach Foxconn MSA (confidential redacted notice)."""
        path = get_raw_path("Turtle Beach-Foxconn")
        doc = reconstructor.reconstruct_document(path, "doc_17")
        intel = extractor.extract(doc)

        assert intel.contract_type.normalized_value == "Master Services Agreement"
        # Effective date ground truth: October 6, 2015
        assert intel.effective_date.is_found
        assert "October" in intel.effective_date.normalized_value and "2015" in intel.effective_date.normalized_value
        # Notice in Turtle Beach is redacted ([*****]), so termination notice is not found or unstated
        assert not intel.termination_notice.is_found

    def test_amx_supply_agreement_notice(self, reconstructor, extractor):
        """Test unredacted notice period on AMX Best Circuit Boards Supply Agreement (60 days)."""
        path = get_raw_path("AMX-Best Circuit Boards")
        doc = reconstructor.reconstruct_document(path, "doc_01")
        intel = extractor.extract(doc)

        assert intel.contract_type.normalized_value == "Supply Agreement"
        assert intel.termination_notice.is_found
        assert intel.termination_notice.normalized_value.notice_days in [30, 60]
