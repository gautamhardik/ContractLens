"""Targeted Unit Tests for Agent Router (Phase 18).

Tests:
1. Routing of direct graph relational queries (parties, payment terms, renewal, termination notice).
2. Routing of direct retrieval queries (clause details).
3. Routing of contract details queries.
4. Routing of obligation queries.
5. Routing of timeline/lifecycle queries.
6. Routing of amendment queries.
7. Routing of multi-condition hybrid reasoning queries.
8. Routing of unanswerable queries to the safe UNANSWERABLE category.
"""

from src.agent.router import AgentRouter
from src.agent.models import AgentRouteCategory
from src.agent.understanding import ContractRoleOntology, CanonicalRole
from src.catalog.catalog import ContractCatalog
from src.models.canonical import CanonicalDocument
import pytest


@pytest.fixture(autouse=True)
def setup_test_catalog():
    ContractRoleOntology._TEST_ROLE_PROVENANCE = {
        "doc_01": {CanonicalRole.SUPPLIER: ["BEST CIRCUIT BOARDS, INC."], CanonicalRole.CUSTOMER: ["AMX, LLC"]},
        "doc_02": {CanonicalRole.SERVICE_PROVIDER: ["Access Worldwide Communications, Inc."], CanonicalRole.CUSTOMER: ["E*TRADE Financial Corporation"]},
        "doc_03": {CanonicalRole.SERVICE_PROVIDER: ["Access Worldwide Communications, Inc."], CanonicalRole.CUSTOMER: ["E*TRADE Financial Corporation"]},
    }
    yield
    ContractRoleOntology._TEST_ROLE_PROVENANCE = {}


def test_route_direct_graph_queries():
    """Test 1: Graph query detection and parameter extraction."""
    route, params = AgentRouter.route_query("Which contracts involve E*TRADE?")
    assert route == AgentRouteCategory.DIRECT_GRAPH
    assert params["query_type"] == "contracts_for_party"
    assert params["param"] == "E*TRADE"

    route2, params2 = AgentRouter.route_query("Which contracts have Net 30 payment terms?")
    assert route2 == AgentRouteCategory.DIRECT_GRAPH
    assert params2["query_type"] == "contracts_with_payment_term"
    assert params2["param"] == "30"

    route3, params3 = AgentRouter.route_query("Which agreements have renewal provisions?")
    assert route3 == AgentRouteCategory.DIRECT_GRAPH
    assert params3["query_type"] == "contracts_with_renewal"

    route4, params4 = AgentRouter.route_query("Which contracts specify termination notice of 30 days?")
    assert route4 == AgentRouteCategory.DIRECT_GRAPH
    assert params4["query_type"] == "contracts_with_termination_notice"
    assert params4["param"] == "30"


def test_route_direct_retrieval():
    """Test 2: Specific clause and text questions route to direct retrieval."""
    route, params = AgentRouter.route_query("What does the indemnification section say about third-party claims?")
    assert route == AgentRouteCategory.DIRECT_RETRIEVAL
    assert "top_k" in params


def test_route_contract_details():
    """Test 3: Contract overview and details queries."""
    route, params = AgentRouter.route_query("What are the payment terms in the Access agreement?")
    assert route == AgentRouteCategory.CONTRACT_DETAILS
    assert params["document_id"] == "doc_03"


def test_route_obligation_queries():
    """Test 4: Obligation questions route to OBLIGATION_QUERY."""
    route, params = AgentRouter.route_query("What obligations does the vendor have under the AMX agreement?")
    assert route == AgentRouteCategory.OBLIGATION_QUERY
    assert params["document_id"] == "doc_01"


def test_route_timeline_queries():
    """Test 5: Expiration and lifecycle questions route to TIMELINE_QUERY."""
    route, params = AgentRouter.route_query("When does the Access agreement expire?")
    assert route == AgentRouteCategory.TIMELINE_QUERY
    assert params["document_id"] == "doc_03"


def test_route_amendment_queries():
    """Test 6: Amendment-related questions route to AMENDMENT_QUERY."""
    route, params = AgentRouter.route_query("What changed in the Access-E*TRADE amendment?")
    assert route == AgentRouteCategory.AMENDMENT_QUERY
    assert params["document_id"] == "doc_02"


def test_route_hybrid_reasoning():
    """Test 7: Multi-condition questions route to HYBRID_REASONING."""
    route, params = AgentRouter.route_query("Which contracts involving E*TRADE have Net 30 payment terms?")
    assert route == AgentRouteCategory.HYBRID_REASONING
    assert params["party"] == "E*TRADE"
    assert params["payment_term"] == "30"


def test_route_unanswerable_safety():
    """Test 8: Out-of-corpus queries route to UNANSWERABLE."""
    route, params = AgentRouter.route_query("Tell me something not contained in the contracts, like the CEO personal salary.")
    assert route == AgentRouteCategory.UNANSWERABLE
