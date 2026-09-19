"""Agent Executor and Multi-Step Orchestrator for ContractLens (Phase 18).

Enforces execution invariants:
1. MAX_STEPS = 6, MAX_TOOL_CALLS = 6, MAX_RETRIES = 1
2. Provenance preservation: Every fact and evidence span is propagated to final verification
3. No private chain-of-thought in AgentTrace: Records tool inputs, outputs, and status only
4. Controlled grounding bridge: Synthesizes final answers exclusively through Phase 16 Grounded RAG
"""

import time
from typing import List, Dict, Any, Optional

from src.models.canonical import EvidenceReference
from src.evidence.models import EvidenceBundle, EvidenceSpan, EvidenceCitation
from src.rag.models import ClaimVerificationStatus, VerificationReport, GroundedAnswer
from src.agent.models import (
    ToolCall,
    ToolResult,
    ToolStatus,
    AgentStep,
    AgentTrace,
    AgentResponse,
    AgentRouteCategory,
)
from src.agent.tools import ToolRegistry, BuildGroundedAnswerArgs
from src.graph.query import QueryResultItem


class AgentExecutor:
    """Safe, bounded tool execution engine for ContractLens."""

    MAX_STEPS = 6
    MAX_TOOL_CALLS = 6
    MAX_RETRIES = 1

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def execute_plan(
        self,
        query: str,
        route: AgentRouteCategory,
        plan_calls: List[ToolCall],
        context: Any = None
    ) -> AgentResponse:
        """Execute a list of planned tool calls under strict guardrails."""
        start_exec = time.perf_counter()
        steps: List[AgentStep] = []
        accumulated_evidence: List[EvidenceReference] = []
        accumulated_citations: List[EvidenceCitation] = []
        accumulated_spans: List[EvidenceSpan] = []
        active_bundle: Optional[EvidenceBundle] = None
        graph_results: List[QueryResultItem] = []

        calls_executed = 0
        step_number = 1

        for call in plan_calls:
            # Check hard limits
            if calls_executed >= self.MAX_TOOL_CALLS or step_number > self.MAX_STEPS:
                step = AgentStep(
                    step_number=step_number,
                    tool_call=call,
                    result=ToolResult(
                        call_id=call.call_id or f"call_{step_number}",
                        tool_name=call.tool_name,
                        status=ToolStatus.LIMIT_EXCEEDED,
                        error_message="Maximum tool execution limit exceeded."
                    )
                )
                steps.append(step)
                break

            # Execute tool safely
            res: ToolResult = self.registry.execute_tool(call, context)
            calls_executed += 1

            # Accumulate evidence and citations
            if res.evidence:
                accumulated_evidence.extend(res.evidence)
            if res.citations:
                accumulated_citations.extend(res.citations)

            # Check specific tool outputs
            if isinstance(res.output, EvidenceBundle):
                active_bundle = res.output
                accumulated_spans.extend(res.output.evidence_spans)
            elif isinstance(res.output, list) and res.output and isinstance(res.output[0], QueryResultItem):
                graph_results.extend(res.output)
                # Convert graph QueryResultItems to EvidenceSpans for grounding
                for item in res.output:
                    if item.evidence:
                        span = EvidenceSpan(
                            document_id=item.evidence.document_id,
                            filename=item.evidence.filename,
                            page_number=item.evidence.page_number,
                            block_id=item.evidence.block_id,
                            reading_order=0,
                            raw_text=f"{item.entity_label}: {item.matched_property} = {item.matched_value}",
                            normalized_text=f"{item.entity_label}: {item.matched_property} = {item.matched_value}",
                            bbox=item.evidence.bbox,
                            block_type="fact",
                            is_table=False
                        )
                        accumulated_spans.append(span)
            elif res.tool_name in ("get_contract_obligations", "get_contract_timeline", "get_contract_details", "get_contract_amendments", "compare_contract_amendments") and res.evidence:
                # Convert structured facts and commitments into evidence spans
                for idx, ev in enumerate(res.evidence):
                    if isinstance(res.output, list) and idx < len(res.output):
                        item_dict = res.output[idx]
                        desc = item_dict.get("action") or item_dict.get("summary") or item_dict.get("description") or item_dict.get("title") or str(item_dict)
                    elif isinstance(res.output, dict):
                        desc = res.output.get("preserved_provisions_summary") or f"{res.output.get('contract_type')}: Payment terms {res.output.get('payment_terms')}, Governing law {res.output.get('governing_law')}"
                    else:
                        desc = "Contractual obligation or amendment modification"
                    
                    span = EvidenceSpan(
                        document_id=ev.document_id,
                        filename=ev.filename,
                        page_number=ev.page_number,
                        block_id=ev.block_id,
                        reading_order=0,
                        raw_text=f"{desc} in {ev.filename}",
                        normalized_text=f"{desc} in {ev.filename}",
                        bbox=ev.bbox,
                        block_type="fact",
                        is_table=False
                    )
                    accumulated_spans.append(span)

            steps.append(AgentStep(step_number=step_number, tool_call=call, result=res))
            step_number += 1

        # Synthesize final answer via build_grounded_answer tool
        grounding_bundle = active_bundle
        if not grounding_bundle:
            # Assemble bundle from accumulated spans and citations
            grounding_bundle = EvidenceBundle(
                query=query,
                retrieved_chunks=[],
                evidence_spans=accumulated_spans,
                citations=accumulated_citations,
                validation_reports=[],
                is_fully_valid=True,
                total_spans=len(accumulated_spans),
                valid_citations_count=len(accumulated_citations)
            )

        ground_call = ToolCall(
            tool_name="build_grounded_answer",
            arguments={"query": query, "evidence_bundle": grounding_bundle, "graph_results": graph_results},
            call_id="call_final_grounding"
        )
        ground_res: ToolResult = self.registry.execute_tool(ground_call, context)
        steps.append(AgentStep(step_number=step_number, tool_call=ground_call, result=ground_res))

        total_lat = (time.perf_counter() - start_exec) * 1000.0

        trace = AgentTrace(
            query=query,
            route=route,
            steps=steps,
            total_latency_ms=total_lat,
            total_tool_calls=len(steps)
        )

        final_grounded: Optional[GroundedAnswer] = ground_res.output if isinstance(ground_res.output, GroundedAnswer) else None

        if final_grounded:
            return AgentResponse(
                query=query,
                answer=final_grounded.answer_text,
                grounding_status=final_grounded.grounding_status,
                citations=final_grounded.citations,
                trace=trace,
                verification_report=final_grounded.verification_report,
                is_insufficient_evidence=final_grounded.is_insufficient_evidence,
                metadata={"total_steps": len(steps)}
            )
        else:
            return AgentResponse(
                query=query,
                answer="The available contract evidence does not establish this.",
                grounding_status=ClaimVerificationStatus.INSUFFICIENT_EVIDENCE,
                citations=[],
                trace=trace,
                is_insufficient_evidence=True,
                metadata={"error": ground_res.error_message or "Grounding failure"}
            )
