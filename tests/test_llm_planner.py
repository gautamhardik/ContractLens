"""Unit and Integration Tests for LLM Tool Planner & Trace Visibility (Phase 41)."""

import json
from unittest.mock import MagicMock

from src.agent.models import AgentRouteCategory, ToolCall
from src.agent.llm_planner import LLMToolPlanner
from src.agent.executor import AgentExecutor
from src.agent.tools import ToolRegistry
from src.rag.generator import FakeLLMProvider


def test_llm_planner_valid_proposal():
    """Verify that LLMToolPlanner parses structured tool proposals."""
    mock_llm = FakeLLMProvider()
    canned_plan = {
        "action_summary": "Searching Foxconn termination clause",
        "tool_calls": [
            {
                "tool_name": "search_contract_evidence",
                "arguments": {"query": "termination notice", "top_k": 3}
            }
        ]
    }
    mock_llm.generate = MagicMock(return_value=json.dumps(canned_plan))

    planner = LLMToolPlanner(llm_provider=mock_llm)
    calls = planner.plan(
        query="What is the notice period?",
        route=AgentRouteCategory.DIRECT_RETRIEVAL,
        route_params={}
    )

    assert len(calls) == 1
    assert calls[0].tool_name == "search_contract_evidence"
    assert calls[0].arguments["top_k"] == 3


def test_llm_planner_filters_illegal_tools():
    """Verify that invalid tools proposed by the LLM are filtered and fall back safely."""
    mock_llm = FakeLLMProvider()
    canned_plan = {
        "action_summary": "Attempting illegal action",
        "tool_calls": [
            {
                "tool_name": "delete_all_contracts",
                "arguments": {}
            }
        ]
    }
    mock_llm.generate = MagicMock(return_value=json.dumps(canned_plan))

    planner = LLMToolPlanner(llm_provider=mock_llm)
    calls = planner.plan(
        query="What is the agreement?",
        route=AgentRouteCategory.DIRECT_RETRIEVAL,
        route_params={"top_k": 5}
    )

    # Illegal tool filtered out -> falls back to deterministic planner
    assert len(calls) == 1
    assert calls[0].tool_name == "search_contract_evidence"


def test_executor_invokes_step_callback():
    """Verify that AgentExecutor triggers step_callback with clean action labels."""
    from src.agent.models import ToolResult, ToolStatus
    registry = ToolRegistry()
    mock_tool = MagicMock()
    mock_tool.name = "search_contract_evidence"
    mock_result = ToolResult(
        call_id="call_1",
        tool_name="search_contract_evidence",
        status=ToolStatus.SUCCESS,
        evidence=[],
        citations=[],
        output=None
    )
    mock_tool.execute.return_value = mock_result
    registry.register(mock_tool)

    executor = AgentExecutor(registry)
    captured_steps = []

    def callback(tool_name, label):
        captured_steps.append((tool_name, label))

    plan = [
        ToolCall(
            tool_name="search_contract_evidence",
            arguments={"query": "Foxconn", "_action_summary": "Searching Foxconn agreement evidence"}
        )
    ]

    executor.execute_plan(
        query="Foxconn query",
        route=AgentRouteCategory.DIRECT_RETRIEVAL,
        plan_calls=plan,
        step_callback=callback
    )

    assert len(captured_steps) == 1
    assert captured_steps[0][0] == "search_contract_evidence"
    assert captured_steps[0][1] == "Searching Foxconn agreement evidence"
