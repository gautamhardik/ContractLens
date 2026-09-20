"""Top-Level ContractLens Agent Facade (Phase 18).

Provides:
- ContractAgent: The primary agent entry point orchestrating routing, planning, and execution.
"""

from typing import Optional, Dict, Any, List

from src.models.canonical import CanonicalDocument
from src.models.intelligence import ContractIntelligence
from src.models.obligation import ContractObligation, LifecycleEvent
from src.retrieval.fusion import HybridRRFRetriever
from src.evidence.resolver import EvidenceResolver
from src.graph.query import ContractGraphQueryEngine
from src.rag.generator import GroundedAnswerGenerator, BaseLLMProvider
from src.agent.models import AgentResponse, AgentRouteCategory
from src.agent.tools import (
    ToolRegistry,
    SearchContractEvidenceTool,
    QueryContractGraphTool,
    GetContractDetailsTool,
    GetContractObligationsTool,
    GetContractTimelineTool,
    GetContractAmendmentsTool,
    CompareDocumentsTool,
    BuildGroundedAnswerTool,
    AgentContext,
)
from src.agent.router import AgentRouter
from src.agent.planner import BaseAgentPlanner, DeterministicPlanner
from src.agent.executor import AgentExecutor
from src.agent.understanding import ContractQueryUnderstander


class ContractAgent:
    """The controlled ContractLens operational intelligence agent."""

    def __init__(
        self,
        retriever: HybridRRFRetriever,
        resolver: EvidenceResolver,
        query_engine: ContractGraphQueryEngine,
        intel_map: Dict[str, ContractIntelligence],
        obligations: List[ContractObligation],
        events: List[LifecycleEvent],
        llm_provider: BaseLLMProvider,
        planner: Optional[BaseAgentPlanner] = None,
    ):
        self.retriever = retriever
        self.resolver = resolver
        self.query_engine = query_engine
        self.intel_map = intel_map
        self.obligations = obligations
        self.events = events
        self.llm_provider = llm_provider
        self.planner = planner or DeterministicPlanner()

        # Build context
        self.context = AgentContext(
            documents=resolver.doc_map,
            intelligences=intel_map,
            obligations=obligations,
            events=events,
        )

        # Build and populate ToolRegistry
        self.registry = ToolRegistry()
        self._register_default_tools()

        # Build executor
        self.executor = AgentExecutor(self.registry)

    def _register_default_tools(self) -> None:
        """Register the 8 core typed contract tools."""
        self.registry.register(SearchContractEvidenceTool(self.retriever, self.resolver))
        self.registry.register(QueryContractGraphTool(self.query_engine))
        self.registry.register(GetContractDetailsTool(self.intel_map))
        self.registry.register(GetContractObligationsTool(self.obligations))
        self.registry.register(GetContractTimelineTool(self.events))
        self.registry.register(GetContractAmendmentsTool(self.intel_map))
        self.registry.register(CompareDocumentsTool(self.intel_map, self.obligations))
        self.registry.register(BuildGroundedAnswerTool(GroundedAnswerGenerator(self.llm_provider)))

    def process_query(
        self,
        query: str,
        catalog: Optional[Any] = None,
        document_id: Optional[str] = None,
        step_callback: Optional[Any] = None
    ) -> AgentResponse:
        # If catalog not provided explicitly, derive it from agent runtime context
        if catalog is None and hasattr(self, "context") and self.context.documents:
            try:
                from src.catalog.catalog import ContractCatalog
                catalog = ContractCatalog.from_runtime(
                    documents=self.context.documents,
                    intelligences=self.intel_map or self.context.intelligences
                )
            except Exception:
                catalog = None

        # 1. Deterministic Query Understanding
        understanding = ContractQueryUnderstander.analyze_query(
            query=query,
            catalog=catalog,
            target_document_id=document_id
        )

        # 2. Deterministic Rule-First Routing
        route, route_params = AgentRouter.route_query(
            query=query,
            catalog=catalog,
            understanding=understanding
        )

        # If user explicitly scoped a document_id, ensure route_params respects it
        if document_id and "document_id" in route_params and not route_params["document_id"]:
            route_params["document_id"] = document_id

        # 3. Plan Tool Invocations
        plan_calls = self.planner.plan(query, route, route_params)

        # Update context catalog snapshot for this turn
        if catalog is not None:
            self.context.catalog = catalog

        # 4. Controlled Execution with Guardrails & Verification
        response = self.executor.execute_plan(
            query=query,
            route=route,
            plan_calls=plan_calls,
            context=self.context,
            step_callback=step_callback,
        )

        # Attach understanding summary to response metadata for traceability
        response.metadata["understanding"] = {
            "intent": understanding.intent.value,
            "target_document_id": understanding.target_document_id,
            "roles": [r.model_dump() for r in understanding.role_candidates],
            "entities": [e.model_dump() for e in understanding.entity_references],
            "temporal_cues": [t.model_dump() for t in understanding.temporal_cues],
            "comparison": understanding.comparison_cue.model_dump() if understanding.comparison_cue else None,
            "expanded_query": understanding.expanded_query.expanded_query,
        }

        return response
