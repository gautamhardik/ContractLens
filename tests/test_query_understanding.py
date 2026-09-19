"""Targeted Unit Tests for Contract Query Understanding Layer & Canonical Entity Ontology (Phase 19).

Tests:
1. vendor -> SUPPLIER canonical mapping and contract-scoped resolution
2. supplier -> SUPPLIER canonical mapping
3. buyer -> BUYER canonical mapping
4. customer/client alias resolution to CUSTOMER
5. explicit corporate party entity extraction
6. ambiguous role (multiple parties claiming role in document) -> AMBIGUOUS status, no guessing
7. unknown role -> UNRESOLVED status
8. temporal expression with known anchor
9. temporal expression with unanchored offset (no date fabrication)
10. amendment intent detection
11. comparison intent detection
12. original query preservation invariant
13. deterministic query expansion (no hallucinations, strictly derived terms)
14. Phase 18 q08 regression: "What obligations does the vendor have under the AMX agreement?"
15. Safe rejection: "What obligations does the unknown vendor have under the AMX agreement?"
"""

import pytest

from src.agent.understanding import (
    ContractQueryUnderstander,
    ContractRoleOntology,
    QueryIntent,
    CanonicalRole,
    RoleResolutionStatus,
    TemporalAnchorStatus,
)
from src.agent.router import AgentRouter
from src.agent.models import AgentRouteCategory


def test_1_vendor_to_supplier_resolution():
    """Test 1: 'vendor' maps to CanonicalRole.SUPPLIER and resolves to Best Circuit Boards under AMX."""
    query = "What obligations does the vendor have under the AMX agreement?"
    u = ContractQueryUnderstander.analyze_query(query)
    
    assert len(u.role_candidates) >= 1
    rc = u.role_candidates[0]
    assert rc.surface_form == "vendor"
    assert rc.canonical_role == CanonicalRole.SUPPLIER
    assert rc.status == RoleResolutionStatus.RESOLVED
    assert rc.resolved_party == "BEST CIRCUIT BOARDS, INC."
    assert u.target_document_id == "doc_01"


def test_2_supplier_to_supplier():
    """Test 2: 'supplier' maps to CanonicalRole.SUPPLIER."""
    query = "What does the supplier have to do under the AMX agreement?"
    u = ContractQueryUnderstander.analyze_query(query)
    
    rc = u.role_candidates[0]
    assert rc.surface_form == "supplier"
    assert rc.canonical_role == CanonicalRole.SUPPLIER
    assert rc.status == RoleResolutionStatus.RESOLVED
    assert rc.resolved_party == "BEST CIRCUIT BOARDS, INC."


def test_3_buyer_to_buyer():
    """Test 3: 'buyer' maps to CanonicalRole.BUYER and resolves to AMX, LLC."""
    query = "What are the buyer's covenants in the AMX agreement?"
    u = ContractQueryUnderstander.analyze_query(query)
    
    rc = u.role_candidates[0]
    assert rc.surface_form == "buyer"
    assert rc.canonical_role == CanonicalRole.BUYER
    assert rc.status == RoleResolutionStatus.RESOLVED
    assert rc.resolved_party == "AMX, LLC"


def test_4_customer_client_alias():
    """Test 4: 'customer' and 'client' map to CanonicalRole.CUSTOMER."""
    u_cust = ContractQueryUnderstander.analyze_query("What must the customer pay?")
    assert u_cust.role_candidates[0].canonical_role == CanonicalRole.CUSTOMER

    u_client = ContractQueryUnderstander.analyze_query("What must the client do?")
    assert u_client.role_candidates[0].canonical_role == CanonicalRole.CUSTOMER


def test_5_explicit_corporate_party():
    """Test 5: Explicit corporate entities are extracted accurately."""
    query = "Which contracts involving E*TRADE have Net 30 payment terms?"
    u = ContractQueryUnderstander.analyze_query(query)
    
    entity_names = [e.canonical_name for e in u.entity_references]
    assert "E*TRADE Financial Corporation" in entity_names
    assert u.intent == QueryIntent.CROSS_CONTRACT


def test_6_ambiguous_role_no_guessing():
    """Test 6: When multiple parties claim a role, the status is AMBIGUOUS and resolved_party is None."""
    # Temporarily register a multi-party contract fixture in ontology
    ContractRoleOntology.CONTRACT_ROLE_PROVENANCE["doc_ambig"] = {
        CanonicalRole.SUPPLIER: ["Vendor One Inc", "Vendor Two LLC"]
    }
    status, party, notes = ContractRoleOntology.resolve_role_for_contract(CanonicalRole.SUPPLIER, "doc_ambig")
    
    assert status == RoleResolutionStatus.AMBIGUOUS
    assert party is None
    assert "Multiple parties claim SUPPLIER" in notes


def test_7_unknown_role():
    """Test 7: A role with no party associated in the contract returns UNRESOLVED."""
    status, party, notes = ContractRoleOntology.resolve_role_for_contract(CanonicalRole.LENDER, "doc_01")
    assert status == RoleResolutionStatus.UNRESOLVED
    assert party is None
    assert "No party associated" in notes


def test_8_temporal_expression_recurring():
    """Test 8: Recurring temporal cues are structured without fabricating dates."""
    query = "What monthly reporting duties does the vendor have?"
    u = ContractQueryUnderstander.analyze_query(query)
    
    assert len(u.temporal_cues) >= 1
    t_cue = u.temporal_cues[0]
    assert t_cue.temporal_type == "recurring"
    assert t_cue.raw_expression == "monthly"
    assert t_cue.resolved_date is None  # No fake date


def test_9_temporal_expression_unanchored_offset():
    """Test 9: Relative offset ('30 days before renewal') remains unanchored without known date."""
    query = "Must notice be given 30 days before renewal?"
    u = ContractQueryUnderstander.analyze_query(query)
    
    assert len(u.temporal_cues) >= 1
    t_cue = u.temporal_cues[0]
    assert t_cue.temporal_type == "offset"
    assert t_cue.offset_days == -30
    assert "renewal" in t_cue.anchor_event
    assert t_cue.anchor_status == TemporalAnchorStatus.UNANCHORED
    assert t_cue.resolved_date is None  # Never fabricated


def test_10_amendment_intent():
    """Test 10: 'What changed in the Access amendment?' is classified as AMENDMENT intent."""
    query = "What changed in the Access amendment?"
    u = ContractQueryUnderstander.analyze_query(query)
    
    assert u.intent == QueryIntent.AMENDMENT
    assert u.comparison_cue is not None
    assert u.comparison_cue.comparison_type == "amendment_change"


def test_11_comparison_intent():
    """Test 11: Explicit cross-contract comparison is recognized."""
    query = "Compare payment terms between AMX and Access"
    u = ContractQueryUnderstander.analyze_query(query)
    
    assert u.intent == QueryIntent.COMPARISON
    assert u.comparison_cue is not None
    assert u.comparison_cue.comparison_type == "multi_contract"


def test_12_original_query_preservation():
    """Test 12: Invariant check - original query is preserved byte-for-byte."""
    raw = "  What obligations does the vendor have under the AMX agreement?  "
    u = ContractQueryUnderstander.analyze_query(raw)
    
    assert u.original_query == raw.strip()
    assert u.expanded_query.original_query == raw.strip()


def test_13_deterministic_query_expansion():
    """Test 13: Query expansion strictly includes verified domain terms and entities."""
    query = "What obligations does the vendor have under the AMX agreement?"
    u = ContractQueryUnderstander.analyze_query(query)
    
    exp = u.expanded_query
    assert "BEST CIRCUIT BOARDS, INC." in exp.expansion_terms
    assert "AMX, LLC" in exp.expansion_terms
    assert "shall" in exp.expansion_terms
    assert exp.original_query in exp.expanded_query


def test_14_phase18_q08_regression_with_router():
    """Test 14: Router receives QueryUnderstanding and routes q08 to OBLIGATION_QUERY with resolved party."""
    query = "What obligations does the vendor have under the AMX agreement?"
    u = ContractQueryUnderstander.analyze_query(query)
    route, params = AgentRouter.route_query(query, understanding=u)

    assert route == AgentRouteCategory.OBLIGATION_QUERY
    assert params["document_id"] == "doc_01"
    assert params["party"] == "vendor"
    assert params["resolved_party"] == "BEST CIRCUIT BOARDS, INC."
    assert "understanding" in params


def test_15_safe_rejection_unknown_vendor():
    """Test 15: Explicit 'unknown vendor' query remains unresolved and routes with party='unknown'."""
    query = "What obligations does the unknown vendor have under the AMX agreement?"
    u = ContractQueryUnderstander.analyze_query(query)
    
    assert len(u.role_candidates) >= 1
    assert u.role_candidates[0].canonical_role == CanonicalRole.UNKNOWN
    assert u.role_candidates[0].status == RoleResolutionStatus.UNRESOLVED

    route, params = AgentRouter.route_query(query, understanding=u)
    assert route == AgentRouteCategory.OBLIGATION_QUERY
    assert params["party"] == "unknown"
