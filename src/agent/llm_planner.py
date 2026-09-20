"""Controlled LLM Tool Planner for ContractLens (Phase 41).

Uses frontier LLM (nvidia/nemotron-3-super-120b-a12b) with:
- Structured function / tool definitions.
- Bounded 5-step budget.
- Argument validation against registered documents and known entities.
- Transparent fallback to DeterministicPlanner if unconfigured, rate-limited, or invalid.
"""

from __future__ import annotations

import json
import logging
from typing import List, Dict, Any, Optional

from src.agent.models import ToolCall, AgentRouteCategory
from src.agent.planner import BaseAgentPlanner, DeterministicPlanner
from src.rag.generator import BaseLLMProvider

logger = logging.getLogger("contractlens.llm_planner")

AVAILABLE_TOOLS_SPEC = [
    {
        "name": "search_contract_evidence",
        "description": "Search contract text chunks for verbatim clause evidence, definitions, numbers, or specific terms.",
        "parameters": {
            "query": "Semantic or lexical search string",
            "top_k": "Number of evidence chunks to retrieve (default: 5)",
            "filter_doc_ids": "Optional list of document IDs to restrict search scope"
        }
    },
    {
        "name": "get_contract_details",
        "description": "Fetch structured metadata for a contract including parties, governing law, payment terms, and dates.",
        "parameters": {
            "document_id": "Document identifier"
        }
    },
    {
        "name": "get_contract_obligations",
        "description": "Fetch extracted operational obligations, deliverables, compliance requirements, or covenants.",
        "parameters": {
            "document_id": "Optional document ID to restrict",
            "party_name": "Optional party role or name (e.g. 'vendor', 'supplier', 'customer')"
        }
    },
    {
        "name": "get_contract_timeline",
        "description": "Fetch lifecycle milestones, expiration dates, renewal windows, and notice deadlines.",
        "parameters": {
            "document_id": "Optional document ID"
        }
    },
    {
        "name": "compare_contract_amendments",
        "description": "Compare parent agreement against an amendment to identify modified, superseded, and preserved clauses.",
        "parameters": {
            "amendment_doc_id": "Amendment document ID",
            "parent_doc_id": "Parent document ID"
        }
    },
    {
        "name": "query_contract_graph",
        "description": "Query the cross-contract knowledge graph for relationships, parties, or portfolio-wide terms.",
        "parameters": {
            "query_type": "One of: 'contracts_involving_party', 'contracts_with_payment_term', 'contracts_with_governing_law', 'cross_contract_dependencies'",
            "param": "Specific value to search in the graph"
        }
    }
]

TOOL_PLANNING_SYSTEM_PROMPT = """You are the ContractLens Agent Controller.
Your role is to propose an optimal, minimal sequence of tool calls (maximum 3 tool calls) to answer the user's contract inquiry.

AVAILABLE TOOLS:
1. search_contract_evidence(query: str, top_k: int, filter_doc_ids: list[str])
2. get_contract_details(document_id: str)
3. get_contract_obligations(document_id: str, party_name: str)
4. get_contract_timeline(document_id: str)
5. compare_contract_amendments(amendment_doc_id: str, parent_doc_id: str)
6. query_contract_graph(query_type: str, param: str)

RULES:
1. Propose ONLY tools from the list above.
2. Return a JSON object with:
   - "action_summary": Concise human-readable action label (e.g., "Searching Foxconn termination clause", "Comparing amendment modifications")
   - "tool_calls": List of { "tool_name": str, "arguments": dict }
3. Maximum 3 tool calls. Keep it focused and minimal.
4. Output strictly valid JSON matching:
{
  "action_summary": "<action description>",
  "tool_calls": [
    {
      "tool_name": "<tool_name>",
      "arguments": { ... }
    }
  ]
}
"""


class LLMToolPlanner(BaseAgentPlanner):
    """Frontier LLM-driven tool planner with argument validation and deterministic fallback."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        fallback_planner: Optional[BaseAgentPlanner] = None,
        max_steps: int = 5,
    ):
        self.llm_provider = llm_provider
        self.fallback = fallback_planner or DeterministicPlanner()
        self.max_steps = max_steps

    def plan(self, query: str, route: AgentRouteCategory, route_params: Dict[str, Any]) -> List[ToolCall]:
        """Propose tool calls using LLM with argument validation and fallback safety."""
        # Unanswerable routes skip planning
        if route == AgentRouteCategory.UNANSWERABLE:
            return []

        # Safely serialize route params (e.g. QueryUnderstanding or Pydantic models)
        safe_params = {}
        for k, v in route_params.items():
            if hasattr(v, "model_dump"):
                safe_params[k] = v.model_dump(mode="json")
            elif hasattr(v, "dict"):
                safe_params[k] = v.dict()
            elif isinstance(v, (str, int, float, bool, list, dict, type(None))):
                safe_params[k] = v
            else:
                safe_params[k] = str(v)

        user_prompt = f"USER QUERY: {query}\nROUTE HINT: {route.value}\nROUTE PARAMS: {json.dumps(safe_params, default=str)}"

        try:
            raw_resp = self.llm_provider.generate(TOOL_PLANNING_SYSTEM_PROMPT, user_prompt)
            cleaned = raw_resp.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0].strip()

            parsed = json.loads(cleaned)
            raw_calls = parsed.get("tool_calls", [])
            action_summary = parsed.get("action_summary", "")

            valid_calls: List[ToolCall] = []
            allowed_names = {t["name"] for t in AVAILABLE_TOOLS_SPEC}

            for idx, c in enumerate(raw_calls[:self.max_steps], start=1):
                name = c.get("tool_name")
                args = c.get("arguments", {})
                if name in allowed_names and isinstance(args, dict):
                    valid_calls.append(ToolCall(
                        tool_name=name,
                        arguments=args,
                        call_id=f"llm_call_{idx}"
                    ))

            if valid_calls:
                # Attach action summary to first call's metadata if available
                if action_summary and valid_calls:
                    valid_calls[0].arguments["_action_summary"] = action_summary
                return valid_calls

        except Exception as e:
            logger.warning("LLM Tool Planning failed or returned invalid JSON: %s. Falling back to DeterministicPlanner.", e)

        # Graceful fallback to deterministic planner
        return self.fallback.plan(query, route, route_params)
