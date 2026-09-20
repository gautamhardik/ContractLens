"""Agent Planner Abstraction and Implementations for ContractLens (Phase 18).

Provides:
- BaseAgentPlanner: Abstract interface generating structured tool calls.
- DeterministicPlanner: Rule-based planner decomposing routed queries into controlled tool calls.
- FakeAgentPlanner: Test-focused planner supporting canned, malformed, multi-step, or invalid plans.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from src.agent.models import ToolCall, AgentRouteCategory


class BaseAgentPlanner(ABC):
    """Abstract interface for planning tool calls."""

    @abstractmethod
    def plan(self, query: str, route: AgentRouteCategory, route_params: Dict[str, Any]) -> List[ToolCall]:
        """Generate ordered sequence of ToolCalls for a given query and route."""
        pass


class DeterministicPlanner(BaseAgentPlanner):
    """Rule-based, zero-cost deterministic planner."""

    def plan(self, query: str, route: AgentRouteCategory, route_params: Dict[str, Any]) -> List[ToolCall]:
        calls: List[ToolCall] = []

        if route == AgentRouteCategory.DIRECT_GRAPH:
            qt = route_params.get("query_type", "contracts_with_payment_term")
            param = route_params.get("param")
            calls.append(ToolCall(
                tool_name="query_contract_graph",
                arguments={"query_type": qt, "param": param},
                call_id="call_graph_1"
            ))

        elif route == AgentRouteCategory.DIRECT_RETRIEVAL:
            top_k = route_params.get("top_k", 5)
            calls.append(ToolCall(
                tool_name="search_contract_evidence",
                arguments={"query": query, "top_k": top_k},
                call_id="call_search_1"
            ))

        elif route == AgentRouteCategory.CONTRACT_DETAILS:
            doc_id = route_params.get("document_id")
            calls.append(ToolCall(
                tool_name="get_contract_details",
                arguments={"document_id": doc_id} if doc_id else {},
                call_id="call_details_1"
            ))
            # Also retrieve substantive clause text (recitals, purpose, scope) for rich answers
            calls.append(ToolCall(
                tool_name="search_contract_evidence",
                arguments={"query": query, "top_k": 3, "filter_doc_ids": [doc_id] if doc_id else None},
                call_id="call_details_search_2"
            ))

        elif route == AgentRouteCategory.OBLIGATION_QUERY:
            doc_id = route_params.get("document_id")
            party = route_params.get("party")
            calls.append(ToolCall(
                tool_name="get_contract_obligations",
                arguments={"document_id": doc_id, "party_name": party},
                call_id="call_ob_1"
            ))

        elif route == AgentRouteCategory.TIMELINE_QUERY:
            doc_id = route_params.get("document_id")
            calls.append(ToolCall(
                tool_name="get_contract_timeline",
                arguments={"document_id": doc_id},
                call_id="call_time_1"
            ))

        elif route == AgentRouteCategory.AMENDMENT_QUERY:
            doc_id = route_params.get("document_id")
            calls.append(ToolCall(
                tool_name="get_contract_amendments",
                arguments={"parent_document_id": doc_id} if doc_id else {},
                call_id="call_amend_1"
            ))
            # Also retrieve supporting evidence for amendment
            calls.append(ToolCall(
                tool_name="search_contract_evidence",
                arguments={"query": query, "top_k": 3},
                call_id="call_search_amend_2"
            ))

        elif route == AgentRouteCategory.HYBRID_REASONING:
            party = route_params.get("party", "E*TRADE")
            term = route_params.get("payment_term", "30")
            # Step 1: Query contracts for party
            calls.append(ToolCall(
                tool_name="query_contract_graph",
                arguments={"query_type": "contracts_for_party", "param": party},
                call_id="call_hybrid_party_1"
            ))
            # Step 2: Query contracts with payment term
            calls.append(ToolCall(
                tool_name="query_contract_graph",
                arguments={"query_type": "contracts_with_payment_term", "param": term},
                call_id="call_hybrid_payment_2"
            ))

        elif route == AgentRouteCategory.UNANSWERABLE:
            # Unanswerable route: Do not retrieve irrelevant noisy chunks; proceed directly to grounding with empty bundle
            # which reliably triggers the Phase 16 controlled insufficient evidence state
            pass

        elif route == AgentRouteCategory.COMPARISON_QUERY:
            calls.append(ToolCall(
                tool_name="compare_documents",
                arguments={},
                call_id="call_compare_1"
            ))

        return calls


class FakeAgentPlanner(BaseAgentPlanner):
    """Configurable mock planner for testing agent guardrails and error recovery."""

    def __init__(self, predefined_plans: Optional[Dict[str, List[ToolCall]]] = None):
        self.predefined_plans = predefined_plans or {}

    def set_plan_for_query(self, query: str, calls: List[ToolCall]) -> None:
        self.predefined_plans[query.strip().lower()] = calls

    def plan(self, query: str, route: AgentRouteCategory, route_params: Dict[str, Any]) -> List[ToolCall]:
        q_lower = query.strip().lower()
        for k, v in self.predefined_plans.items():
            if k in q_lower:
                return v
        # Default to deterministic fallback
        return DeterministicPlanner().plan(query, route, route_params)
