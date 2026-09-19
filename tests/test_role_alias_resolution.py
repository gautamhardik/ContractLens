"""Targeted Unit Tests for Conversational Role-Alias Resolution (Phase 18.1).

Validates:
1. "What obligations does the vendor have under the AMX agreement?" -> resolves role 'vendor' -> Supplier obligations
2. "What does the supplier have to do under the AMX agreement?" -> resolves role 'supplier' -> Supplier obligations
3. "What are the vendor's obligations under the AMX agreement?" -> resolves role 'vendor' -> Supplier obligations
4. "What does AMX have to do under the AMX agreement?" -> resolves party 'AMX' -> Customer obligations
5. "What obligations does Best Circuit Boards have?" -> resolves party 'Best Circuit Boards' -> Supplier obligations
6. Safety boundary: "What obligations does the unknown vendor have under the AMX agreement?" -> does not resolve to supplier -> 0 matches & safe insufficient evidence
"""

import pytest

from src.agent.router import AgentRouter
from src.agent.models import AgentRouteCategory, ToolCall, ToolStatus
from src.agent.tools import ToolRegistry, GetContractObligationsTool, BuildGroundedAnswerTool
from src.agent.executor import AgentExecutor
from src.ingestion.reconstructor import StructuralReconstructor
from src.ingestion.extractor import ContractIntelligenceExtractor
from src.ingestion.obligation_extractor import ObligationExtractor
from src.rag.generator import GroundedAnswerGenerator, FakeLLMProvider
from tests.test_canonical_reconstruction import get_raw_path


@pytest.fixture(scope="module")
def amx_obligations():
    reconstructor = StructuralReconstructor()
    extractor = ContractIntelligenceExtractor()
    ob_extractor = ObligationExtractor()

    doc = reconstructor.reconstruct_document(get_raw_path("AMX-Best Circuit Boards Supply Agreement.pdf"), "doc_01")
    intel = extractor.extract(doc)
    return ob_extractor.extract_obligations(doc, intel)


@pytest.fixture(scope="module")
def agent_executor(amx_obligations):
    reg = ToolRegistry()
    reg.register(GetContractObligationsTool(amx_obligations))
    reg.register(BuildGroundedAnswerTool(GroundedAnswerGenerator(FakeLLMProvider())))
    return AgentExecutor(reg)


def test_route_vendor_obligation_query():
    """Verify routing extracts conversational role 'vendor' instead of falling back to 'AMX'."""
    query = "What obligations does the vendor have under the AMX agreement?"
    route, params = AgentRouter.route_query(query)
    assert route == AgentRouteCategory.OBLIGATION_QUERY
    assert params["document_id"] == "doc_01"
    assert params["party"] == "vendor"


def test_route_supplier_obligation_query():
    """Verify routing extracts role 'supplier'."""
    query = "What does the supplier have to do under the AMX agreement?"
    route, params = AgentRouter.route_query(query)
    assert route == AgentRouteCategory.OBLIGATION_QUERY
    assert params["document_id"] == "doc_01"
    assert params["party"] == "supplier"


def test_route_possessive_vendor_obligations():
    """Verify routing handles possessive 'vendor's obligations'."""
    query = "What are the vendor's obligations under the AMX agreement?"
    route, params = AgentRouter.route_query(query)
    assert route == AgentRouteCategory.OBLIGATION_QUERY
    assert params["document_id"] == "doc_01"
    assert params["party"] == "vendor"


def test_route_explicit_entity_obligation_query():
    """Verify routing preserves exact corporate entity when specified."""
    query_amx = "What does AMX have to do under the AMX agreement?"
    route_amx, params_amx = AgentRouter.route_query(query_amx)
    assert route_amx == AgentRouteCategory.OBLIGATION_QUERY
    assert params_amx["document_id"] == "doc_01"
    assert params_amx["party"] == "AMX"

    query_bcb = "What obligations does Best Circuit Boards have?"
    route_bcb, params_bcb = AgentRouter.route_query(query_bcb)
    assert route_bcb == AgentRouteCategory.OBLIGATION_QUERY
    assert params_bcb["party"] == "Best Circuit Boards"


def test_route_unknown_vendor_safety():
    """Verify that 'unknown vendor' is explicitly kept as 'unknown' and not mapped to a valid role."""
    query = "What obligations does the unknown vendor have under the AMX agreement?"
    route, params = AgentRouter.route_query(query)
    assert route == AgentRouteCategory.OBLIGATION_QUERY
    assert params["document_id"] == "doc_01"
    assert params["party"] == "unknown"


def test_execute_vendor_role_resolves_to_supplier_obligations(agent_executor):
    """Verify executing 'vendor' obligations query yields Supplier commitments with verified grounding."""
    q = "What obligations does the vendor have under the AMX agreement?"
    plan = [
        ToolCall(tool_name="get_contract_obligations", arguments={"document_id": "doc_01", "party_name": "vendor"}, call_id="c1")
    ]
    resp = agent_executor.execute_plan(query=q, route=AgentRouteCategory.OBLIGATION_QUERY, plan_calls=plan)

    step1 = resp.trace.steps[0]
    assert step1.result.status == ToolStatus.SUCCESS
    assert len(step1.result.output) == 7  # 7 Supplier obligations
    assert resp.is_insufficient_evidence is False
    assert len(resp.citations) >= 1
    assert "manufacture" in resp.answer.lower()


def test_execute_unknown_vendor_safe_rejection(agent_executor):
    """Verify executing unknown vendor does not hallucinate and returns insufficient evidence."""
    q = "What obligations does the unknown vendor have under the AMX agreement?"
    plan = [
        ToolCall(tool_name="get_contract_obligations", arguments={"document_id": "doc_01", "party_name": "unknown"}, call_id="c2")
    ]
    resp = agent_executor.execute_plan(query=q, route=AgentRouteCategory.OBLIGATION_QUERY, plan_calls=plan)

    step1 = resp.trace.steps[0]
    assert step1.result.status == ToolStatus.NO_RESULTS
    assert len(step1.result.output) == 0
    assert resp.is_insufficient_evidence is True
    assert len(resp.citations) == 0
    assert "does not establish" in resp.answer
