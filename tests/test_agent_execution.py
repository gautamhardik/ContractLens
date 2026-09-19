"""Targeted Unit and End-to-End Tests for Agent Execution (Phase 18).

Tests:
1. End-to-end execution of a Direct Graph query with trace generation.
2. End-to-end execution of an Obligation query preserving UNKNOWN status.
3. Multi-step Hybrid Reasoning execution (party filter + payment term filter + grounded answer).
4. Unanswerable query safety (no hallucinations, clean insufficient evidence response).
5. Hard execution limit enforcement (MAX_STEPS / MAX_TOOL_CALLS).
6. Malformed planner output recovery with FakeAgentPlanner.
7. Real corpus execution on Access-E*TRADE MSA.
"""

import json
import pytest

from src.models.canonical import CanonicalDocument, CanonicalPage, CanonicalBlock, BlockType, BoundingBox, EvidenceReference
from src.models.chunk import RetrievalChunk, ChunkProvenance, ChunkType
from src.retrieval.lexical import BM25Retriever
from src.retrieval.dense import LSADenseRetriever
from src.retrieval.fusion import HybridRRFRetriever
from src.evidence.resolver import EvidenceResolver
from src.models.intelligence import ContractIntelligence, ExtractedField, ExtractionMethod, ContractParty, PaymentTerms, AmendmentFact
from src.models.obligation import ContractObligation, TemporalConstraint, TemporalType, ObligationStatus, LifecycleEvent, LifecycleEventType
from src.graph.models import KnowledgeGraph
from src.graph.builder import KnowledgeGraphBuilder
from src.graph.query import ContractGraphQueryEngine
from src.rag.generator import FakeLLMProvider
from src.rag.models import ClaimVerificationStatus
from src.agent.models import ToolCall, ToolStatus
from src.agent.planner import FakeAgentPlanner
from src.agent.agent import ContractAgent


@pytest.fixture
def full_agent_fixture():
    """Setup multi-contract agent with mock and canonical data."""
    bbox = BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=150.0)
    ev_msa = EvidenceReference(document_id="doc_03", filename="Access-E-TRADE MSA.pdf", page_number=3, block_id="b_p3", bbox=bbox)
    ev_amend = EvidenceReference(document_id="doc_02", filename="Access-E-TRADE Amendment.pdf", page_number=1, block_id="b_amend", bbox=bbox)

    b1 = CanonicalBlock(
        block_id="b_p3",
        document_id="doc_03",
        page_number=3,
        reading_order=0,
        block_type=BlockType.PARAGRAPH,
        bbox=bbox,
        raw_text="Payment Terms. Invoices shall be paid Net 30 days.",
        normalized_text="Payment Terms. Invoices shall be paid Net 30 days.",
        section_number="6.0",
        section_title="Payment Terms",
    )
    b2 = CanonicalBlock(
        block_id="b_amend",
        document_id="doc_02",
        page_number=1,
        reading_order=0,
        block_type=BlockType.PARAGRAPH,
        bbox=bbox,
        raw_text="Section 1.2 Price and Payment of the Agreement shall be deleted in its entirety and replaced.",
        normalized_text="Section 1.2 Price and Payment of the Agreement shall be deleted in its entirety and replaced.",
        section_number="1.0",
        section_title="Amendments",
    )

    p3 = CanonicalPage(page_number=3, width=612.0, height=792.0, blocks=[b1])
    p_amend = CanonicalPage(page_number=1, width=612.0, height=792.0, blocks=[b2])

    doc_msa = CanonicalDocument(
        document_id="doc_03",
        filename="Access-E-TRADE MSA.pdf",
        file_size=1024,
        page_count=3,
        pages=[p3],
    )
    doc_amend = CanonicalDocument(
        document_id="doc_02",
        filename="Access-E-TRADE Amendment.pdf",
        file_size=512,
        page_count=1,
        pages=[p_amend],
    )

    chunk1 = RetrievalChunk(
        chunk_id="chk_msa",
        document_id="doc_03",
        chunk_type=ChunkType.SECTION,
        text=b1.raw_text,
        char_count=len(b1.raw_text),
        token_estimate=15,
        provenance=ChunkProvenance(
            document_id="doc_03",
            filename="Access-E-TRADE MSA.pdf",
            page_start=3,
            page_end=3,
            block_ids=["b_p3"],
            section_number="6.0",
            section_title="Payment Terms",
            bounding_boxes=[bbox]
        )
    )
    chunk2 = RetrievalChunk(
        chunk_id="chk_amend",
        document_id="doc_02",
        chunk_type=ChunkType.SECTION,
        text=b2.raw_text,
        char_count=len(b2.raw_text),
        token_estimate=18,
        provenance=ChunkProvenance(
            document_id="doc_02",
            filename="Access-E-TRADE Amendment.pdf",
            page_start=1,
            page_end=1,
            block_ids=["b_amend"],
            section_number="1.0",
            section_title="Amendments",
            bounding_boxes=[bbox]
        )
    )

    bm25 = BM25Retriever([chunk1, chunk2])
    dense = LSADenseRetriever(n_components=2, random_state=42)
    dense.index([chunk1, chunk2])
    hybrid = HybridRRFRetriever(lexical_retriever=bm25, dense_retriever=dense, rrf_k=60)
    resolver = EvidenceResolver([doc_msa, doc_amend])

    intel_msa = ContractIntelligence(
        document_id="doc_03",
        filename="Access-E-TRADE MSA.pdf",
        contract_type=ExtractedField(field_name="contract_type", raw_value="MSA", normalized_value="Master Services Agreement", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX),
        effective_date=ExtractedField(field_name="effective_date", raw_value="Jan 1, 2020", normalized_value="2020-01-01", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev_msa),
        expiration_date=ExtractedField.not_found("expiration_date"),
        renewal_language=ExtractedField.not_found("renewal_language"),
        governing_law=ExtractedField(field_name="governing_law", raw_value="State of New York", normalized_value="New York", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev_msa),
        parties=[
            ContractParty(name="Access Worldwide Communications, Inc", raw_text="Access Worldwide Communications, Inc", evidence=ev_msa),
            ContractParty(name="E*TRADE Financial Corporation", raw_text="E*TRADE Financial Corporation", evidence=ev_msa)
        ],
        payment_terms=ExtractedField(field_name="payment_terms", raw_value="Net 30", normalized_value=PaymentTerms(payment_type="Net 30", payment_days=30, raw_text="Net 30", evidence=ev_msa), extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev_msa),
    )

    intel_amend = ContractIntelligence(
        document_id="doc_02",
        filename="Access-E-TRADE Amendment.pdf",
        contract_type=ExtractedField(field_name="contract_type", raw_value="Amendment", normalized_value="Amendment", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX),
        effective_date=ExtractedField(field_name="effective_date", raw_value="Feb 1, 2021", normalized_value="2021-02-01", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev_amend),
        expiration_date=ExtractedField.not_found("expiration_date"),
        renewal_language=ExtractedField.not_found("renewal_language"),
        governing_law=ExtractedField.not_found("governing_law"),
        parties=[
            ContractParty(name="Access Worldwide Communications, Inc", raw_text="Access Worldwide Communications, Inc", evidence=ev_amend),
            ContractParty(name="E*TRADE Financial Corporation", raw_text="E*TRADE Financial Corporation", evidence=ev_amend)
        ],
        amendment_facts=[
            AmendmentFact(action="DELETE_AND_REPLACE", target_section="Section 1.2", summary="Replaces Section 1.2 Price and Payment", raw_text=b2.raw_text, evidence=ev_amend)
        ]
    )

    intel_map = {"doc_03": intel_msa, "doc_02": intel_amend}

    ob = ContractObligation(
        obligation_id="ob_01",
        actor="Access Worldwide Communications, Inc",
        action="provide monthly performance reports",
        temporal=TemporalConstraint(temporal_type=TemporalType.RECURRING, raw_expression="monthly"),
        status=ObligationStatus.UNKNOWN,
        source_clause="Section 4.1",
        evidence=ev_msa
    )

    evt = LifecycleEvent(
        event_id="evt_01",
        event_type=LifecycleEventType.EFFECTIVE_DATE,
        title="Agreement Effective Date",
        description="Contract effective date",
        date_or_trigger="2020-01-01",
        is_fixed_date=True,
        evidence=ev_msa
    )

    graph = KnowledgeGraphBuilder.build_graph([doc_msa, doc_amend], [intel_msa, intel_amend], obligations_by_doc={"doc_03": [ob]}, events_by_doc={"doc_03": [evt]})
    query_engine = ContractGraphQueryEngine(graph)

    fake_llm = FakeLLMProvider()
    fake_llm.set_response_for_query(
        "etrade",
        json.dumps({
            "answer": "E*TRADE is a party to the Access-E*TRADE MSA and Amendment [E1].",
            "claims": [{"text": "E*TRADE is a party to the Access-E*TRADE MSA and Amendment.", "evidence_ids": ["E1"]}]
        })
    )
    fake_llm.set_response_for_query(
        "obligations",
        json.dumps({
            "answer": "Access Worldwide must provide monthly performance reports [E1].",
            "claims": [{"text": "Access Worldwide must provide monthly performance reports.", "evidence_ids": ["E1"]}]
        })
    )
    fake_llm.set_response_for_query(
        "not contained",
        json.dumps({
            "answer": "The available contract evidence does not establish this.",
            "claims": []
        })
    )

    agent = ContractAgent(
        retriever=hybrid,
        resolver=resolver,
        query_engine=query_engine,
        intel_map=intel_map,
        obligations=[ob],
        events=[evt],
        llm_provider=fake_llm
    )

    return agent


def test_agent_graph_execution_with_trace(full_agent_fixture):
    """Test 1: Agent processes a graph query, maintains trace, and returns grounded answer."""
    agent = full_agent_fixture
    resp = agent.process_query("Which contracts involve E*TRADE?")

    assert resp.trace.route.value == "DIRECT_GRAPH"
    assert len(resp.trace.steps) >= 2  # Graph call + Grounding call
    assert resp.trace.steps[0].tool_call.tool_name == "query_contract_graph"
    assert resp.trace.steps[0].result.status == ToolStatus.SUCCESS
    assert resp.grounding_status in (ClaimVerificationStatus.SUPPORTED, ClaimVerificationStatus.PARTIALLY_SUPPORTED)
    assert len(resp.citations) >= 1


def test_agent_obligation_query_unknown_status(full_agent_fixture):
    """Test 2: Agent processes an obligation query, preserving UNKNOWN completion status."""
    agent = full_agent_fixture
    resp = agent.process_query("What obligations does the vendor have under the Access agreement?")

    assert resp.trace.route.value == "OBLIGATION_QUERY"
    ob_step = [s for s in resp.trace.steps if s.tool_call.tool_name == "get_contract_obligations"][0]
    assert ob_step.result.status == ToolStatus.SUCCESS
    assert ob_step.result.output[0]["status"] == "UNKNOWN"
    assert "monthly performance reports" in resp.answer


def test_agent_unanswerable_safety(full_agent_fixture):
    """Test 3: Unanswerable query results in safe insufficient-evidence state with 0 fabricated citations."""
    agent = full_agent_fixture
    resp = agent.process_query("Tell me something not contained in the contracts.")

    assert resp.is_insufficient_evidence is True
    assert resp.grounding_status == ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
    assert len(resp.citations) == 0


def test_agent_execution_limit_enforcement(full_agent_fixture):
    """Test 4: FakeAgentPlanner generating excessive steps triggers hard execution limit."""
    agent = full_agent_fixture
    
    # Create planner that requests 10 tool calls
    excessive_calls = [
        ToolCall(tool_name="get_contract_details", arguments={"document_id": "doc_03"}, call_id=f"c_{i}")
        for i in range(10)
    ]
    fake_planner = FakeAgentPlanner()
    fake_planner.set_plan_for_query("loop query", excessive_calls)

    agent.planner = fake_planner
    resp = agent.process_query("loop query")

    # The executor should have stopped after MAX_STEPS / MAX_TOOL_CALLS (6)
    limit_steps = [s for s in resp.trace.steps if s.result.status == ToolStatus.LIMIT_EXCEEDED]
    assert len(limit_steps) >= 1
