"""ContractLens Agent Package (Phase 18).

Exposes the core agent layer:
- ContractAgent: The primary operational reasoning facade.
- ToolRegistry & AgentTool: Strongly typed tool framework.
- AgentRouter: Deterministic rule-first router.
- DeterministicPlanner & FakeAgentPlanner: Plan generators.
- AgentExecutor: Step-bounded orchestrator.
- AgentModels: ToolCall, ToolResult, AgentStep, AgentTrace, AgentResponse.
"""

from src.agent.models import (
    ToolStatus,
    AgentRouteCategory,
    ToolCall,
    ToolResult,
    AgentStep,
    AgentTrace,
    AgentResponse,
)
from src.agent.tools import (
    AgentTool,
    ToolRegistry,
    SearchContractEvidenceTool,
    QueryContractGraphTool,
    GetContractDetailsTool,
    GetContractObligationsTool,
    GetContractTimelineTool,
    GetContractAmendmentsTool,
    CompareContractAmendmentsTool,
    BuildGroundedAnswerTool,
    AgentContext,
)
from src.agent.router import AgentRouter
from src.agent.planner import (
    BaseAgentPlanner,
    DeterministicPlanner,
    FakeAgentPlanner,
)
from src.agent.executor import AgentExecutor
from src.agent.agent import ContractAgent
from src.agent.understanding import (
    QueryIntent,
    CanonicalRole,
    RoleResolutionStatus,
    RoleCandidate,
    EntityReference,
    TemporalCue,
    ComparisonCue,
    ExpandedQuery,
    QueryUnderstanding,
    ContractRoleOntology,
    ContractQueryUnderstander,
)

__all__ = [
    "ToolStatus",
    "AgentRouteCategory",
    "ToolCall",
    "ToolResult",
    "AgentStep",
    "AgentTrace",
    "AgentResponse",
    "AgentTool",
    "ToolRegistry",
    "SearchContractEvidenceTool",
    "QueryContractGraphTool",
    "GetContractDetailsTool",
    "GetContractObligationsTool",
    "GetContractTimelineTool",
    "GetContractAmendmentsTool",
    "CompareContractAmendmentsTool",
    "BuildGroundedAnswerTool",
    "AgentContext",
    "AgentRouter",
    "BaseAgentPlanner",
    "DeterministicPlanner",
    "FakeAgentPlanner",
    "AgentExecutor",
    "ContractAgent",
    "QueryIntent",
    "CanonicalRole",
    "RoleResolutionStatus",
    "RoleCandidate",
    "EntityReference",
    "TemporalCue",
    "ComparisonCue",
    "ExpandedQuery",
    "QueryUnderstanding",
    "ContractRoleOntology",
    "ContractQueryUnderstander",
]
