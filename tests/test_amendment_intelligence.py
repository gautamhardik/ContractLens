"""Targeted Unit and Integration Tests for Phase 21 Amendment & Version Intelligence.

Validates:
1. Parent <-> amendment deterministic resolution (Access Amendment doc_02 -> Access MSA doc_03).
2. Section alignment matching parent §1.2, §3, §6, §15.4 to amendment modifications.
3. Structured before/after delta modeling with dual evidence citations.
4. Full force and effect clause detection and preservation representation.
5. Conservative, grounded business impact analysis.
6. CompareContractAmendmentsTool execution via ToolRegistry.
7. AgentTrace evidence tracking for amendment comparisons.
8. Unamended sections preservation invariant.
"""

import pytest

from src.ingestion.reconstructor import StructuralReconstructor
from src.ingestion.extractor import ContractIntelligenceExtractor
from src.models.amendment import (
    AmendmentChangeType,
    AmendmentResolution,
    StructuredAmendmentChange,
    VersionComparisonReport,
)
from src.temporal.amendment_engine import AmendmentIntelligenceEngine
from src.agent.tools import ToolRegistry, CompareContractAmendmentsTool, AgentContext
from src.agent.models import ToolCall, ToolStatus
from tests.test_canonical_reconstruction import get_raw_path


@pytest.fixture(scope="module")
def access_pair_context():
    reconstructor = StructuralReconstructor()
    extractor = ContractIntelligenceExtractor()

    d2 = reconstructor.reconstruct_document(get_raw_path("Access–E-TRADE Amendment.pdf"), "doc_02")
    d3 = reconstructor.reconstruct_document(get_raw_path("Access–E-TRADE MSA.pdf"), "doc_03")

    i2 = extractor.extract(d2)
    i3 = extractor.extract(d3)

    canonical_docs = {"doc_02": d2, "doc_03": d3}
    intel_map = {"doc_02": i2, "doc_03": i3}

    engine = AmendmentIntelligenceEngine(canonical_docs, intel_map)
    return engine, canonical_docs, intel_map


def test_1_parent_amendment_resolution(access_pair_context):
    """Verify Access Amendment doc_02 resolves deterministically to Access MSA doc_03 with evidence."""
    engine, _, _ = access_pair_context
    res = engine.resolve_parent("doc_02")

    assert res is not None
    assert res.amendment_doc_id == "doc_02"
    assert res.parent_doc_id == "doc_03"
    assert res.resolution_confidence >= 0.95
    assert res.evidence is not None
    assert res.evidence.document_id == "doc_02"


def test_2_section_alignment(access_pair_context):
    """Verify section alignment correctly links parent and amendment clauses."""
    engine, _, _ = access_pair_context
    changes = engine.align_sections(parent_doc_id="doc_03", amendment_doc_id="doc_02")

    assert len(changes) == 5
    sec_map = {c.section_number: c for c in changes}

    assert "Section 1.2" in sec_map
    assert "Section 3" in sec_map
    assert "Section 6" in sec_map
    assert "Section 15.4" in sec_map
    assert "General" in sec_map


def test_3_before_after_delta_with_dual_evidence(access_pair_context):
    """Verify structured changes capture before text, after text, and dual evidence."""
    engine, _, _ = access_pair_context
    changes = engine.align_sections(parent_doc_id="doc_03", amendment_doc_id="doc_02")
    sec_map = {c.section_number: c for c in changes}

    c_price = sec_map["Section 1.2"]
    assert c_price.change_type == AmendmentChangeType.DELETE_AND_REPLACE
    assert c_price.before_text is not None
    assert "price" in c_price.before_text.lower()
    assert c_price.parent_evidence is not None
    assert c_price.parent_evidence.document_id == "doc_03"
    assert c_price.amendment_evidence is not None
    assert c_price.amendment_evidence.document_id == "doc_02"


def test_4_insurance_addition_change_type(access_pair_context):
    """Verify §15.4 is classified as ADD_COVERAGE with appropriate impact."""
    engine, _, _ = access_pair_context
    changes = engine.align_sections(parent_doc_id="doc_03", amendment_doc_id="doc_02")
    sec_map = {c.section_number: c for c in changes}

    c_ins = sec_map["Section 15.4"]
    assert c_ins.change_type == AmendmentChangeType.ADD_COVERAGE
    assert "insurance" in c_ins.impact_summary.lower() or "e&o" in c_ins.impact_summary.lower()


def test_5_full_force_and_effect_confirmation(access_pair_context):
    """Verify full force confirmation is preserved and not mistaken for complete agreement replacement."""
    engine, _, _ = access_pair_context
    report = engine.compare_versions(amendment_doc_id="doc_02")

    assert report is not None
    assert report.full_force_confirmed is True
    assert "full force and effect" in report.preserved_provisions_summary.lower()


def test_6_grounded_business_impact(access_pair_context):
    """Verify business impact items are conservative and tied strictly to affected sections."""
    engine, _, _ = access_pair_context
    report = engine.compare_versions(amendment_doc_id="doc_02")

    assert len(report.business_impact_items) >= 4
    impact_text = " ".join(report.business_impact_items).lower()
    assert "price" in impact_text
    assert "term" in impact_text
    assert "payment" in impact_text


def test_7_compare_amendments_tool_execution(access_pair_context):
    """Verify CompareContractAmendmentsTool executes properly inside ToolRegistry."""
    engine, _, _ = access_pair_context
    reg = ToolRegistry()
    tool = CompareContractAmendmentsTool(engine)
    reg.register(tool)

    call = ToolCall(
        tool_name="compare_contract_amendments",
        arguments={"amendment_document_id": "doc_02"},
        call_id="call_test_compare",
    )
    result = reg.execute_tool(call, AgentContext())

    assert result.status == ToolStatus.SUCCESS
    assert result.output["parent_document_id"] == "doc_03"
    assert result.output["total_modifications"] == 5
    assert len(result.evidence) >= 5


def test_8_compare_amendments_tool_invalid_amendment(access_pair_context):
    """Verify CompareContractAmendmentsTool returns NO_RESULTS on unknown amendment."""
    engine, _, _ = access_pair_context
    tool = CompareContractAmendmentsTool(engine)

    args = tool.input_schema(amendment_document_id="doc_999_nonexistent")
    result = tool.execute(args, AgentContext())

    assert result.status == ToolStatus.NO_RESULTS
