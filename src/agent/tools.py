"""Deterministic Agent Tool Layer for ContractLens (Phase 18).

Implements the typed AgentTool protocol, core tools, and ToolRegistry:
1. search_contract_evidence: Hybrid RRF + EvidenceResolver -> Verified EvidenceBundle
2. query_contract_graph: ContractGraphQueryEngine -> Structured items + EvidenceReferences
3. get_contract_details: ContractIntelligence -> Verified contract metadata
4. get_contract_obligations: ContractObligation -> Filtered commitments (preserving UNKNOWN status)
5. get_contract_timeline: LifecycleEvent -> Milestone dates & unresolved constraints
6. get_contract_amendments: AmendmentFact -> Modification summaries & parent linkage
7. build_grounded_answer: Grounded RAG + ClaimVerifier -> VerifiedAnswer + Citations
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Set
from pydantic import BaseModel, Field, ValidationError, ConfigDict

from src.models.canonical import EvidenceReference, CanonicalDocument
from src.evidence.models import EvidenceBundle, EvidenceCitation
from src.evidence.resolver import EvidenceResolver
from src.retrieval.fusion import HybridRRFRetriever
from src.graph.query import ContractGraphQueryEngine, QueryResultItem
from src.models.intelligence import ContractIntelligence
from src.models.obligation import ContractObligation, LifecycleEvent, ObligationStatus
from src.rag.generator import GroundedAnswerGenerator, BaseLLMProvider
from src.rag.verifier import ClaimVerifier
from src.rag.models import GroundedAnswer, ClaimVerificationStatus, VerificationReport
from src.agent.models import ToolCall, ToolResult, ToolStatus


class AgentContext(BaseModel):
    """Execution context containing loaded repositories and engines."""
    documents: Dict[str, CanonicalDocument] = Field(default_factory=dict)
    intelligences: Dict[str, ContractIntelligence] = Field(default_factory=dict)
    obligations: List[ContractObligation] = Field(default_factory=list)
    events: List[LifecycleEvent] = Field(default_factory=list)
    catalog: Optional[Any] = None
    model_config = ConfigDict(arbitrary_types_allowed=True)


# ==============================================================================
# 1. TOOL SCHEMAS
# ==============================================================================

class SearchEvidenceArgs(BaseModel):
    query: str
    top_k: int = 5
    filter_doc_ids: Optional[List[str]] = None


class QueryGraphArgs(BaseModel):
    query_type: str  # e.g. "contracts_for_party", "contracts_with_payment_term", "contracts_with_renewal", "contracts_with_termination_notice", "amendments_for_contract", "parties_for_contract"
    param: Optional[str] = None


class GetContractDetailsArgs(BaseModel):
    document_id: str


class GetObligationsArgs(BaseModel):
    document_id: Optional[str] = None
    party_name: Optional[str] = None
    action_keyword: Optional[str] = None


class GetTimelineArgs(BaseModel):
    document_id: Optional[str] = None
    event_type: Optional[str] = None


class GetAmendmentsArgs(BaseModel):
    parent_document_id: Optional[str] = None
    amendment_document_id: Optional[str] = None


class CompareDocumentsArgs(BaseModel):
    pass  # No args needed; tool operates over full intel_map in context


class BuildGroundedAnswerArgs(BaseModel):
    query: str
    evidence_bundle: Optional[EvidenceBundle] = None
    graph_results: Optional[List[QueryResultItem]] = None


# ==============================================================================
# 2. BASE TOOL PROTOCOL
# ==============================================================================

class AgentTool(ABC):
    """Abstract contract for an agent tool."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Type[BaseModel]:
        pass

    @abstractmethod
    def execute(self, args: BaseModel, context: Any) -> ToolResult:
        pass


# ==============================================================================
# 3. TOOL IMPLEMENTATIONS
# ==============================================================================

class SearchContractEvidenceTool(AgentTool):
    """Tool retrieving unstructured contractual evidence via Hybrid RRF + EvidenceResolver."""

    def __init__(self, retriever: Any, resolver: EvidenceResolver):
        self.retriever = retriever
        self.resolver = resolver

    @property
    def name(self) -> str:
        return "search_contract_evidence"

    @property
    def description(self) -> str:
        return "Retrieve and resolve contractual evidence spans with bounding boxes for a query."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return SearchEvidenceArgs

    def execute(self, args: SearchEvidenceArgs, context: Any) -> ToolResult:
        t0 = time.perf_counter()
        call_id = f"call_search_{int(t0*1000)}"

        try:
            # Check if retriever accepts retrieval_query from understanding context
            retrieval_kwargs = {"query": args.query, "top_k": args.top_k, "filter_doc_ids": args.filter_doc_ids}
            if hasattr(self.retriever, "retrieve") and hasattr(context, "metadata"):
                und = context.metadata.get("understanding") if isinstance(context.metadata, dict) else None
                if und is not None and hasattr(self.retriever, "enable_adaptive_weights"):
                    from src.retrieval.adaptive import RetrievalQuery
                    retrieval_kwargs["retrieval_query"] = RetrievalQuery.from_understanding(und, target_document_ids=args.filter_doc_ids)

            candidates = self.retriever.retrieve(**retrieval_kwargs)
            chunks = [c for c, _ in candidates]
            bundle = self.resolver.create_evidence_bundle(query=args.query, retrieved_chunks=chunks)

            # Collect evidence references
            ev_refs = [
                EvidenceReference(
                    document_id=s.document_id,
                    filename=s.filename,
                    page_number=s.page_number,
                    block_id=s.block_id,
                    bbox=s.bbox,
                )
                for s in bundle.evidence_spans
            ]

            status = ToolStatus.SUCCESS if bundle.total_spans > 0 else ToolStatus.NO_RESULTS
            lat = (time.perf_counter() - t0) * 1000.0

            return ToolResult(
                call_id=call_id,
                tool_name=self.name,
                status=status,
                output=bundle,
                evidence=ev_refs,
                citations=bundle.citations,
                latency_ms=lat,
                metadata={"total_spans": bundle.total_spans, "is_fully_valid": bundle.is_fully_valid}
            )
        except Exception as e:
            return ToolResult(
                call_id=call_id,
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                error_message=str(e)
            )


class QueryContractGraphTool(AgentTool):
    """Tool querying the typed Contract Knowledge Graph for relational/multi-contract facts."""

    def __init__(self, query_engine: ContractGraphQueryEngine):
        self.query_engine = query_engine

    @property
    def name(self) -> str:
        return "query_contract_graph"

    @property
    def description(self) -> str:
        return "Execute deterministic relational queries against the Contract Knowledge Graph."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return QueryGraphArgs

    def execute(self, args: QueryGraphArgs, context: Any) -> ToolResult:
        t0 = time.perf_counter()
        call_id = f"call_graph_{int(t0*1000)}"

        try:
            qt = args.query_type
            p = args.param or ""
            items: List[QueryResultItem] = []

            if qt == "contracts_for_party":
                items = self.query_engine.get_contracts_for_party(p)
            elif qt == "parties_for_contract":
                items = self.query_engine.get_parties_for_contract(p)
            elif qt == "contracts_with_payment_term":
                items = self.query_engine.get_contracts_with_payment_term(p)
            elif qt == "contracts_with_renewal":
                items = self.query_engine.get_contracts_with_renewal()
            elif qt == "contracts_with_termination_notice":
                days = int(p) if p.isdigit() else None
                items = self.query_engine.get_contracts_with_termination_notice(days)
            elif qt == "amendments_for_contract":
                items = self.query_engine.get_amendments_for_contract(p)
            elif qt == "obligations_for_party":
                items = self.query_engine.get_obligations_for_party(p)
            elif qt == "get_contract":
                c = self.query_engine.get_contract(p)
                if c:
                    items = [QueryResultItem(
                        entity_id=c.node_id,
                        entity_label=c.label,
                        entity_type=c.node_type.value,
                        contract_id=c.properties.get("document_id", p),
                        contract_filename=c.properties.get("filename", c.label),
                        matched_property="contract",
                        matched_value=c.label,
                        evidence=c.evidence,
                    )]
            else:
                return ToolResult(
                    call_id=call_id,
                    tool_name=self.name,
                    status=ToolStatus.INVALID_ARGUMENTS,
                    error_message=f"Unsupported query_type: '{qt}'",
                    latency_ms=(time.perf_counter() - t0) * 1000.0,
                )

            ev_refs = [i.evidence for i in items if i.evidence is not None]
            status = ToolStatus.SUCCESS if items else ToolStatus.NO_RESULTS

            return ToolResult(
                call_id=call_id,
                tool_name=self.name,
                status=status,
                output=items,
                evidence=ev_refs,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                metadata={"query_type": qt, "param": p, "count": len(items)}
            )
        except Exception as e:
            return ToolResult(
                call_id=call_id,
                tool_name=self.name,
                status=ToolStatus.FAILURE,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                error_message=str(e)
            )


class GetContractDetailsTool(AgentTool):
    """Tool returning verified structured contract intelligence."""

    def __init__(self, intel_map: Dict[str, ContractIntelligence]):
        self.intel_map = intel_map

    @property
    def name(self) -> str:
        return "get_contract_details"

    @property
    def description(self) -> str:
        return "Retrieve structured metadata, parties, governing law, and payment terms for a contract."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return GetContractDetailsArgs

    def execute(self, args: GetContractDetailsArgs, context: Any) -> ToolResult:
        t0 = time.perf_counter()
        call_id = f"call_details_{int(t0*1000)}"

        did = args.document_id.strip()
        intel = self.intel_map.get(did)
        if not intel:
            # Check by filename substring
            for k, v in self.intel_map.items():
                if did.lower() in v.filename.lower() or did.lower() in k.lower():
                    intel = v
                    break

        if not intel:
            return ToolResult(
                call_id=call_id,
                tool_name=self.name,
                status=ToolStatus.NO_RESULTS,
                error_message=f"No contract intelligence found for: '{did}'",
                latency_ms=(time.perf_counter() - t0) * 1000.0,
            )

        ev_refs: List[EvidenceReference] = []
        if intel.effective_date.evidence:
            ev_refs.append(intel.effective_date.evidence)
        if intel.governing_law.evidence:
            ev_refs.append(intel.governing_law.evidence)
        for p in intel.parties:
            if p.evidence:
                ev_refs.append(p.evidence)
        if intel.payment_terms and intel.payment_terms.evidence:
            ev_refs.append(intel.payment_terms.evidence)
        if intel.termination_notice and intel.termination_notice.evidence:
            ev_refs.append(intel.termination_notice.evidence)

        data = {
            "document_id": intel.document_id,
            "filename": intel.filename,
            "contract_type": intel.contract_type.normalized_value,
            "parties": [{"name": p.name, "role": p.role, "jurisdiction": p.jurisdiction} for p in intel.parties],
            "effective_date": intel.effective_date.normalized_value,
            "expiration_date": intel.expiration_date.normalized_value,
            "governing_law": intel.governing_law.normalized_value,
            "payment_terms": intel.payment_terms.normalized_value.payment_type if (intel.payment_terms and intel.payment_terms.is_found and intel.payment_terms.normalized_value) else None,
            "termination_notice_days": intel.termination_notice.normalized_value.notice_days if (intel.termination_notice and intel.termination_notice.is_found and intel.termination_notice.normalized_value) else None,
            "renewal_language": intel.renewal_language.normalized_value if intel.renewal_language.is_found else None,
            "amendments_count": len(intel.amendment_facts),
        }

        return ToolResult(
            call_id=call_id,
            tool_name=self.name,
            status=ToolStatus.SUCCESS,
            output=data,
            evidence=ev_refs,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            metadata={"document_id": intel.document_id}
        )


class GetContractObligationsTool(AgentTool):
    """Tool retrieving operational commitments, preserving UNKNOWN completion status."""

    def __init__(self, obligations: List[ContractObligation]):
        self.obligations = obligations

    @property
    def name(self) -> str:
        return "get_contract_obligations"

    @property
    def description(self) -> str:
        return "Retrieve operational obligations, actors, actions, and temporal constraints."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return GetObligationsArgs

    ROLE_SYNONYMS = {
        "vendor": {"vendor", "supplier", "provider", "manufacturer", "contractor"},
        "supplier": {"supplier", "vendor", "provider", "manufacturer"},
        "manufacturer": {"manufacturer", "supplier", "vendor", "provider"},
        "customer": {"customer", "client", "buyer"},
        "client": {"client", "customer", "buyer"},
        "buyer": {"buyer", "customer", "client"},
        "seller": {"seller", "vendor", "supplier"},
    }

    def execute(self, args: GetObligationsArgs, context: Any) -> ToolResult:
        t0 = time.perf_counter()
        call_id = f"call_ob_{int(t0*1000)}"

        matched = self.obligations
        if args.document_id:
            did = args.document_id.lower().strip()
            matched = [o for o in matched if o.evidence.document_id.lower() == did or did in o.evidence.filename.lower()]

        if args.party_name:
            p_lower = args.party_name.lower().strip()
            
            # 1. Resolve role synonyms if party_name is a known role (e.g. 'vendor', 'supplier')
            target_role_terms = self.ROLE_SYNONYMS.get(p_lower, {p_lower})

            # 2. Derive dynamic party-to-role mappings from catalog or context intelligences
            entity_roles: Set[str] = set()
            role_entities: Set[str] = set()

            doc_id_key = args.document_id.lower().strip() if args.document_id else None
            
            # Check context catalog if available
            catalog = getattr(context, "catalog", None)
            if catalog and doc_id_key and hasattr(catalog, "roles") and doc_id_key in catalog.roles:
                doc_roles = catalog.roles[doc_id_key]
                for ent_name, canonical_role in doc_roles.items():
                    ent_key = ent_name.lower().strip()
                    role_str = canonical_role.value.lower()
                    syns = self.ROLE_SYNONYMS.get(role_str, {role_str})
                    if ent_key in p_lower or p_lower in ent_key:
                        entity_roles.update(syns)
                    if any(term in syns or term == role_str for term in target_role_terms):
                        role_entities.add(ent_key)
            elif context and hasattr(context, "intelligences") and doc_id_key:
                intel = context.intelligences.get(doc_id_key)
                if intel and intel.parties:
                    for p in intel.parties:
                        ent_key = p.name.lower().strip()
                        if ent_key in p_lower or p_lower in ent_key:
                            entity_roles.add(p_lower)

            def matches_party_or_role(o: ContractObligation) -> bool:
                actor_lower = o.actor.lower()
                cp_lower = o.counterparty.lower() if o.counterparty else ""

                # Direct match
                if p_lower in actor_lower or p_lower in cp_lower:
                    return True
                
                # Check role synonyms against actor/counterparty
                for term in target_role_terms:
                    if term in actor_lower or term in cp_lower:
                        return True

                # Check entity mapped roles
                for role in entity_roles:
                    if role in actor_lower or role in cp_lower:
                        return True

                # Check role mapped entities
                for ent in role_entities:
                    if ent in actor_lower or ent in cp_lower:
                        return True

                return False

            matched = [o for o in matched if matches_party_or_role(o)]

        if args.action_keyword:
            kw = args.action_keyword.lower().strip()
            matched = [o for o in matched if kw in o.action.lower() or kw in o.temporal.raw_expression.lower()]

        ev_refs = [o.evidence for o in matched]
        status = ToolStatus.SUCCESS if matched else ToolStatus.NO_RESULTS

        # Format output cleanly
        out_items = [
            {
                "obligation_id": o.obligation_id,
                "actor": o.actor,
                "action": o.action,
                "counterparty": o.counterparty,
                "temporal_type": o.temporal.temporal_type.value,
                "raw_expression": o.temporal.raw_expression,
                "status": o.status.value,  # UNKNOWN
                "document_id": o.evidence.document_id,
                "page_number": o.evidence.page_number,
            }
            for o in matched[:50]  # Cap response items safely
        ]

        return ToolResult(
            call_id=call_id,
            tool_name=self.name,
            status=status,
            output=out_items,
            evidence=ev_refs,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            metadata={"total_matched": len(matched)}
        )


class GetContractTimelineTool(AgentTool):
    """Tool retrieving lifecycle milestones without fabricating unresolved calendar dates."""

    def __init__(self, events: List[LifecycleEvent]):
        self.events = events

    @property
    def name(self) -> str:
        return "get_contract_timeline"

    @property
    def description(self) -> str:
        return "Retrieve contractual lifecycle milestones, renewal triggers, and notice deadlines."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return GetTimelineArgs

    def execute(self, args: GetTimelineArgs, context: Any) -> ToolResult:
        t0 = time.perf_counter()
        call_id = f"call_time_{int(t0*1000)}"

        matched = self.events
        if args.document_id:
            matched = [e for e in matched if e.evidence.document_id == args.document_id or args.document_id.lower() in e.evidence.filename.lower()]

        if args.event_type:
            et = args.event_type.lower().strip()
            matched = [e for e in matched if et in e.event_type.value.lower()]

        ev_refs = [e.evidence for e in matched]
        status = ToolStatus.SUCCESS if matched else ToolStatus.NO_RESULTS

        out_items = [
            {
                "event_id": e.event_id,
                "title": e.title,
                "event_type": e.event_type.value,
                "date_or_trigger": e.date_or_trigger,
                "is_fixed_date": e.is_fixed_date,
                "description": e.description,
                "document_id": e.evidence.document_id,
                "page_number": e.evidence.page_number,
            }
            for e in matched
        ]

        return ToolResult(
            call_id=call_id,
            tool_name=self.name,
            status=status,
            output=out_items,
            evidence=ev_refs,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            metadata={"total_matched": len(matched)}
        )


class GetContractAmendmentsTool(AgentTool):
    """Tool retrieving verified amendment modifications and parent relationships."""

    def __init__(self, intel_map: Dict[str, ContractIntelligence]):
        self.intel_map = intel_map

    @property
    def name(self) -> str:
        return "get_contract_amendments"

    @property
    def description(self) -> str:
        return "Retrieve amendment modifications, affected sections, and parent agreement links."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return GetAmendmentsArgs

    def execute(self, args: GetAmendmentsArgs, context: Any) -> ToolResult:
        t0 = time.perf_counter()
        call_id = f"call_amend_{int(t0*1000)}"

        results = []
        ev_refs: List[EvidenceReference] = []

        for doc_id, intel in self.intel_map.items():
            if intel.amendment_facts:
                for af in intel.amendment_facts:
                    results.append({
                        "amendment_doc_id": doc_id,
                        "amendment_filename": intel.filename,
                        "action": af.action,
                        "target_section": af.target_section,
                        "summary": af.summary,
                        "raw_text": af.raw_text,
                        "page_number": af.evidence.page_number,
                    })
                    ev_refs.append(af.evidence)

        if args.parent_document_id:
            pid = args.parent_document_id.lower()
            matching_amend_ids = set()
            if self.context and self.context.catalog and self.context.catalog.amendments:
                for a_id, p_res in self.context.catalog.amendments.items():
                    if p_res.parent_doc_id and p_res.parent_doc_id.lower() == pid:
                        matching_amend_ids.add(a_id)
            if matching_amend_ids:
                results = [r for r in results if r["amendment_doc_id"] in matching_amend_ids]
                ev_refs = [e for e in ev_refs if e.document_id in matching_amend_ids]

        if args.amendment_document_id:
            aid = args.amendment_document_id.lower()
            results = [r for r in results if aid in r["amendment_doc_id"].lower() or aid in r["amendment_filename"].lower()]
            ev_refs = [e for e in ev_refs if aid in e.document_id.lower() or aid in e.filename.lower()]

        status = ToolStatus.SUCCESS if results else ToolStatus.NO_RESULTS

        return ToolResult(
            call_id=call_id,
            tool_name=self.name,
            status=status,
            output=results,
            evidence=ev_refs,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            metadata={"total_modifications": len(results)},
        )


class CompareAmendmentsArgs(BaseModel):
    amendment_document_id: str
    parent_document_id: Optional[str] = None


class CompareContractAmendmentsTool(AgentTool):
    """Tool executing Phase 21 structured parent <-> amendment comparison."""

    def __init__(self, engine: Any):
        self.engine = engine

    @property
    def name(self) -> str:
        return "compare_contract_amendments"

    @property
    def description(self) -> str:
        return "Execute structured before/after amendment comparison, section alignment, and business impact analysis."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return CompareAmendmentsArgs

    def execute(self, args: CompareAmendmentsArgs, context: Any) -> ToolResult:
        t0 = time.perf_counter()
        call_id = f"call_compare_amend_{int(t0*1000)}"

        report = self.engine.compare_versions(
            amendment_doc_id=args.amendment_document_id,
            parent_doc_id=args.parent_document_id,
        )

        if not report:
            return ToolResult(
                call_id=call_id,
                tool_name=self.name,
                status=ToolStatus.NO_RESULTS,
                error_message=f"Could not resolve parent contract for amendment: '{args.amendment_document_id}'",
                latency_ms=(time.perf_counter() - t0) * 1000.0,
            )

        ev_refs: List[EvidenceReference] = [report.resolution.evidence]
        for c in report.changes:
            ev_refs.append(c.amendment_evidence)
            if c.parent_evidence:
                ev_refs.append(c.parent_evidence)
        if report.full_force_evidence:
            ev_refs.append(report.full_force_evidence)

        # Deduplicate evidence refs
        dedup_refs = []
        seen = set()
        for e in ev_refs:
            key = (e.document_id, e.page_number, e.block_id)
            if key not in seen:
                seen.add(key)
                dedup_refs.append(e)

        data = {
            "parent_document_id": report.parent_doc_id,
            "parent_filename": report.parent_filename,
            "amendment_document_id": report.amendment_doc_id,
            "amendment_filename": report.amendment_filename,
            "resolution_confidence": report.resolution.resolution_confidence,
            "resolution_basis": report.resolution.resolution_basis,
            "total_modifications": report.total_modifications,
            "full_force_confirmed": report.full_force_confirmed,
            "preserved_provisions_summary": report.preserved_provisions_summary,
            "business_impact_items": report.business_impact_items,
            "changes": [
                {
                    "change_id": c.change_id,
                    "section_number": c.section_number,
                    "section_title": c.section_title,
                    "change_type": c.change_type.value,
                    "before_text": c.before_text,
                    "after_text": c.after_text,
                    "impact_summary": c.impact_summary,
                }
                for c in report.changes
            ],
        }

        return ToolResult(
            call_id=call_id,
            tool_name=self.name,
            status=ToolStatus.SUCCESS,
            output=data,
            evidence=dedup_refs,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            metadata={"modifications_count": len(report.changes)},
        )



class CompareDocumentsTool(AgentTool):
    """Tool 8: Cross-document intelligence comparison.

    Builds a structured markdown difference table from ContractIntelligence
    metadata (parties, contract type, governing law, payment terms, dates,
    obligations, amendments). Bypasses RAG — uses pre-extracted structured data.
    """

    def __init__(self, intel_map: Dict[str, Any], obligations: List[Any]):
        self.intel_map = intel_map
        self.obligations = obligations

    @property
    def name(self) -> str:
        return "compare_documents"

    @property
    def description(self) -> str:
        return "Build a structured comparison / difference table across all loaded contracts using extracted intelligence."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return CompareDocumentsArgs

    def execute(self, args: CompareDocumentsArgs, context: Any) -> ToolResult:
        t0 = time.perf_counter()
        call_id = f"call_compare_{int(t0*1000)}"

        intel_map = self.intel_map
        # Prefer context's live intel if available
        if context and hasattr(context, "intelligences") and context.intelligences:
            intel_map = context.intelligences

        obligations = self.obligations
        if context and hasattr(context, "obligations") and context.obligations is not None:
            obligations = context.obligations

        if len(intel_map) < 2:
            return ToolResult(
                call_id=call_id,
                tool_name=self.name,
                status=ToolStatus.NO_RESULTS,
                output={"answer": "Only one contract is loaded. Upload at least two contracts to compare them."},
                latency_ms=(time.perf_counter() - t0) * 1000.0,
            )

        rows: List[Dict[str, str]] = []
        ev_refs: List[EvidenceReference] = []

        for doc_id, intel in intel_map.items():
            # Count obligations per document
            ob_count = sum(1 for ob in obligations if ob.evidence.document_id == doc_id)

            # Is this an amendment doc (has amendment_facts)?
            is_amendment = bool(intel.amendment_facts)

            # Resolve parties
            parties_str = ", ".join(p.name for p in intel.parties) if intel.parties else "—"

            # Resolve contract type
            ctype = intel.contract_type.raw_value if intel.contract_type.is_found else "—"

            # Resolve governing law
            gov = intel.governing_law.normalized_value if intel.governing_law.is_found else "—"

            # Resolve payment terms
            pay = intel.payment_terms.raw_value if intel.payment_terms.is_found else "—"

            # Resolve effective date
            eff = intel.effective_date.normalized_value if intel.effective_date.is_found else "—"

            # Resolve expiration date
            exp = intel.expiration_date.normalized_value if intel.expiration_date.is_found else "—"

            # Resolve amendment count
            amend_count = len(intel.amendment_facts) if intel.amendment_facts else 0
            doc_nature = "Amendment" if is_amendment else "Base Agreement"

            rows.append({
                "doc_id": doc_id,
                "filename": intel.filename or doc_id,
                "nature": doc_nature,
                "contract_type": ctype,
                "parties": parties_str,
                "governing_law": gov,
                "payment_terms": pay,
                "effective_date": eff,
                "expiration_date": exp,
                "obligations": str(ob_count),
                "amendment_modifications": str(amend_count) if amend_count else "—",
            })

            # Collect any intelligence-level evidence refs for provenance
            for field_val in [intel.contract_type, intel.governing_law, intel.payment_terms,
                               intel.effective_date, intel.expiration_date]:
                if hasattr(field_val, "is_found") and field_val.is_found and hasattr(field_val, "evidence") and field_val.evidence:
                    ev_refs.append(field_val.evidence)

        # Build markdown comparison table
        attrs = [
            ("Filename", "filename"),
            ("Document Nature", "nature"),
            ("Contract Type", "contract_type"),
            ("Parties", "parties"),
            ("Governing Law", "governing_law"),
            ("Payment Terms", "payment_terms"),
            ("Effective Date", "effective_date"),
            ("Expiration Date", "expiration_date"),
            ("Obligations Extracted", "obligations"),
            ("Amendment Modifications", "amendment_modifications"),
        ]

        # Header row
        header_cols = ["Attribute"] + [r["filename"] for r in rows]
        header = "| " + " | ".join(header_cols) + " |"
        separator = "| " + " | ".join(["---"] * len(header_cols)) + " |"

        table_lines = [header, separator]
        diff_flags = []
        for label, key in attrs:
            values = [r[key] for r in rows]
            has_diff = len(set(v.lower() for v in values)) > 1
            diff_flags.append(has_diff)
            diff_marker = " ⬅ differs" if has_diff else ""
            row_line = f"| **{label}**{diff_marker} | " + " | ".join(values) + " |"
            table_lines.append(row_line)

        table_md = "\n".join(table_lines)

        # Summary sentence
        diff_count = sum(diff_flags)
        total_attrs = len(attrs)
        summary_parts = []
        for (label, key), is_diff in zip(attrs, diff_flags):
            if is_diff:
                vals = " vs. ".join(f"*{r[key]}*" for r in rows)
                summary_parts.append(f"**{label}**: {vals}")

        if summary_parts:
            summary = (
                f"Comparing {len(rows)} contracts: **{diff_count} of {total_attrs} attributes differ**.\n\n"
                + "\n".join(f"- {p}" for p in summary_parts)
            )
        else:
            summary = f"Comparing {len(rows)} contracts: all {total_attrs} extracted attributes are identical across documents."

        answer = f"{summary}\n\n{table_md}"

        # Deduplicate ev_refs
        dedup = []
        seen: Set = set()
        for e in ev_refs:
            k = (e.document_id, e.page_number, e.block_id)
            if k not in seen:
                seen.add(k)
                dedup.append(e)

        return ToolResult(
            call_id=call_id,
            tool_name=self.name,
            status=ToolStatus.SUCCESS,
            output={"answer": answer, "rows": rows, "diff_count": diff_count},
            evidence=dedup,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            metadata={"documents_compared": len(rows), "attributes_differing": diff_count},
        )


class BuildGroundedAnswerTool(AgentTool):
    """Tool executing Phase 16 Grounded RAG + Claim Verification."""

    def __init__(self, generator: GroundedAnswerGenerator):
        self.generator = generator

    @property
    def name(self) -> str:
        return "build_grounded_answer"

    @property
    def description(self) -> str:
        return "Generate grounded natural-language answer with independent claim verification."

    @property
    def input_schema(self) -> Type[BaseModel]:
        return BuildGroundedAnswerArgs

    def execute(self, args: BuildGroundedAnswerArgs, context: Any) -> ToolResult:
        t0 = time.perf_counter()
        call_id = f"call_ground_{int(t0*1000)}"

        bundle = args.evidence_bundle
        if not bundle:
            # Create a minimal empty bundle if none was provided
            bundle = EvidenceBundle(
                query=args.query,
                retrieved_chunks=[],
                evidence_spans=[],
                citations=[],
                validation_reports=[],
                is_fully_valid=True,
                total_spans=0,
                valid_citations_count=0
            )

        # 1. Synthesize candidate answer & claims
        raw_answer, claims, evidence_map, gen_latency = self.generator.generate_candidate_answer(
            query=args.query,
            bundle=bundle
        )

        # 2. Independently verify claims against evidence spans
        report = ClaimVerifier.verify_all_claims(claims=claims, evidence_map=evidence_map)

        # 3. Filter verified citations
        active_citations: List[EvidenceCitation] = []
        seen = set()
        for res in report.results:
            if res.is_supported or res.status == ClaimVerificationStatus.PARTIALLY_SUPPORTED:
                for cit in res.resolved_citations:
                    k = (cit.document_id, cit.page_number, cit.block_id)
                    if k not in seen:
                        active_citations.append(cit)
                        seen.add(k)

        # Check for insufficient evidence refusal
        has_refusal_phrase = (
            "does not establish" in raw_answer.lower()
            or "insufficient evidence" in raw_answer.lower()
            or "no relevant contractual evidence" in raw_answer.lower()
        )
        # An answer is insufficient if it explicitly refused, had claims that failed verification,
        # or had 0 claims AND either has a refusal phrase or an empty/short answer.
        # Informative answers explaining general contractual terms/concepts (len(claims) == 0 with substantive answer) are valid.
        is_insufficient = (
            has_refusal_phrase
            or report.insufficient_evidence_claims > 0
            or (len(claims) == 0 and (len(raw_answer.strip()) < 30 or "not establish" in raw_answer.lower()))
        )

        if is_insufficient:
            status = ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
        elif report.contradicted_claims > 0:
            status = ClaimVerificationStatus.CONTRADICTED
        elif report.unsupported_claims > 0:
            status = ClaimVerificationStatus.UNSUPPORTED
        elif report.partially_supported_claims > 0:
            status = ClaimVerificationStatus.PARTIALLY_SUPPORTED
        else:
            status = ClaimVerificationStatus.SUPPORTED

        grounded_answer = GroundedAnswer(
            query=args.query,
            answer_text=raw_answer,
            claims=claims,
            citations=active_citations,
            verification_report=report,
            is_insufficient_evidence=is_insufficient,
            grounding_status=status
        )

        ev_refs = [
            EvidenceReference(
                document_id=c.document_id,
                filename=c.filename,
                page_number=c.page_number,
                block_id=c.block_id,
                bbox=c.bbox
            )
            for c in active_citations
        ]

        lat = (time.perf_counter() - t0) * 1000.0

        return ToolResult(
            call_id=call_id,
            tool_name=self.name,
            status=ToolStatus.SUCCESS,
            output=grounded_answer,
            evidence=ev_refs,
            citations=active_citations,
            latency_ms=lat,
            metadata={
                "grounding_status": status.value,
                "supported_claims": report.supported_claims,
                "total_claims": report.total_claims,
            }
        )


# ==============================================================================
# 4. TOOL REGISTRY
# ==============================================================================

class ToolRegistry:
    """Central registry providing typed tool lookup and execution."""

    def __init__(self):
        self._tools: Dict[str, AgentTool] = {}

    def register(self, tool: AgentTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[AgentTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "schema": t.input_schema.schema()
            }
            for t in self._tools.values()
        ]

    def execute_tool(self, call: ToolCall, context: Any) -> ToolResult:
        t0 = time.perf_counter()
        tool = self._tools.get(call.tool_name)

        if not tool:
            return ToolResult(
                call_id=call.call_id or "unknown",
                tool_name=call.tool_name,
                status=ToolStatus.UNKNOWN_TOOL,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                error_message=f"Tool '{call.tool_name}' is not registered."
            )

        try:
            # Validate input against typed schema
            validated_args = tool.input_schema(**call.arguments)
        except ValidationError as ve:
            return ToolResult(
                call_id=call.call_id or "invalid_schema",
                tool_name=call.tool_name,
                status=ToolStatus.INVALID_ARGUMENTS,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                error_message=f"Invalid arguments for tool '{call.tool_name}': {ve.errors()}"
            )
        except Exception as e:
            return ToolResult(
                call_id=call.call_id or "invalid_schema",
                tool_name=call.tool_name,
                status=ToolStatus.INVALID_ARGUMENTS,
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                error_message=str(e)
            )

        return tool.execute(validated_args, context)
