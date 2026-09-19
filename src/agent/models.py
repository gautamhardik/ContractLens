"""Agent Data Models for ContractLens (Phase 18).

Defines strongly-typed representations for:
- ToolStatus: Execution outcome status for tool invocations.
- AgentRouteCategory: High-level classification of user intents.
- ToolCall: Invocation request with validated arguments.
- ToolResult: Structured output from tool execution with mandatory provenance.
- AgentStep: Single execution step in an agent run.
- AgentTrace: Multi-step trace of tool activity (without private chain-of-thought).
- AgentResponse: Final verified agent output with grounded answer, citations, and trace.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set, Union
from pydantic import BaseModel, Field

from src.models.canonical import EvidenceReference
from src.evidence.models import EvidenceCitation, EvidenceBundle
from src.rag.models import ClaimVerificationStatus, VerificationReport, GroundedAnswer


class ToolStatus(str, Enum):
    """Outcome status of an agent tool execution."""
    SUCCESS = "success"
    INVALID_ARGUMENTS = "invalid_arguments"
    UNKNOWN_TOOL = "unknown_tool"
    NO_RESULTS = "no_results"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    LIMIT_EXCEEDED = "limit_exceeded"
    FAILURE = "failure"


class AgentRouteCategory(str, Enum):
    """Categorization of query intent for deterministic routing."""
    DIRECT_GRAPH = "DIRECT_GRAPH"
    DIRECT_RETRIEVAL = "DIRECT_RETRIEVAL"
    CONTRACT_DETAILS = "CONTRACT_DETAILS"
    OBLIGATION_QUERY = "OBLIGATION_QUERY"
    TIMELINE_QUERY = "TIMELINE_QUERY"
    AMENDMENT_QUERY = "AMENDMENT_QUERY"
    HYBRID_REASONING = "HYBRID_REASONING"
    UNANSWERABLE = "UNANSWERABLE"


class ToolCall(BaseModel):
    """Specific tool invocation requested by router or planner."""
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    call_id: str = ""


class ToolResult(BaseModel):
    """Structured result returned by an agent tool."""
    call_id: str
    tool_name: str
    status: ToolStatus
    output: Any = None
    evidence: List[EvidenceReference] = Field(default_factory=list)
    citations: List[EvidenceCitation] = Field(default_factory=list)
    latency_ms: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentStep(BaseModel):
    """Record of a single executed agent step."""
    step_number: int
    tool_call: ToolCall
    result: ToolResult


class AgentTrace(BaseModel):
    """Audit trace of all tool interactions during an agent execution."""
    query: str
    route: AgentRouteCategory
    steps: List[AgentStep] = Field(default_factory=list)
    total_latency_ms: float = 0.0
    total_tool_calls: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Final, auditable agent response backed by grounded citations."""
    query: str
    answer: str
    grounding_status: ClaimVerificationStatus
    citations: List[EvidenceCitation] = Field(default_factory=list)
    trace: AgentTrace
    verification_report: Optional[VerificationReport] = None
    is_insufficient_evidence: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
