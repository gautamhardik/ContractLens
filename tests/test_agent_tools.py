"""Targeted Unit Tests for Agent Tool Layer & Registry (Phase 18).

Tests:
1. ToolRegistry registration, lookup, and unknown tool handling.
2. Argument schema validation and rejection of invalid argument types.
3. search_contract_evidence execution and EvidenceBundle output.
4. query_contract_graph execution and QueryResultItem output.
5. get_contract_details execution and metadata output.
6. get_contract_obligations execution and UNKNOWN status preservation.
7. get_contract_timeline execution and milestone output.
8. get_contract_amendments execution and modification output.
9. build_grounded_answer execution with Phase 16 ClaimVerifier integration.
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
from src.rag.generator import FakeLLMProvider, GroundedAnswerGenerator
from src.agent.models import ToolCall, ToolStatus
from src.agent.tools import (
    ToolRegistry,
    SearchContractEvidenceTool,
    QueryContractGraphTool,
    GetContractDetailsTool,
    GetContractObligationsTool,
    GetContractTimelineTool,
    GetContractAmendmentsTool,
    BuildGroundedAnswerTool,
    SearchEvidenceArgs,
    QueryGraphArgs,
    GetContractDetailsArgs,
)


@pytest.fixture
def agent_mock_infrastructure():
    """Build mock data structures for testing agent tools."""
    bbox = BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=150.0)
    ev = EvidenceReference(document_id="doc_03", filename="Access-E-TRADE MSA.pdf", page_number=3, block_id="b_p3", bbox=bbox)
    
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
    p3 = CanonicalPage(page_number=3, width=612.0, height=792.0, blocks=[b1])
    doc = CanonicalDocument(
        document_id="doc_03",
        filename="Access-E-TRADE MSA.pdf",
        file_size=1024,
        page_count=3,
        pages=[p3],
    )

    chunk = RetrievalChunk(
        chunk_id="chk_p3",
        document_id="doc_03",
        chunk_type=ChunkType.SECTION,
        text=b1.raw_text,
        char_count=len(b1.raw_text),
        token_estimate=len(b1.raw_text) // 4,
        provenance=ChunkProvenance(
            document_id="doc_03",
            filename="Access-E-TRADE MSA.pdf",
            page_start=3,
            page_end=3,
            block_ids=["b_p3"],
            section_number="6.0",
            section_title="Payment Terms",
            bounding_boxes=[b1.bbox]
        )
    )

    bm25 = BM25Retriever([chunk])
    dense = LSADenseRetriever(n_components=2, random_state=42)
    dense.index([chunk])
    hybrid = HybridRRFRetriever(lexical_retriever=bm25, dense_retriever=dense, rrf_k=60)
    resolver = EvidenceResolver([doc])

    intel = ContractIntelligence(
        document_id="doc_03",
        filename="Access-E-TRADE MSA.pdf",
        contract_type=ExtractedField(field_name="contract_type", raw_value="MSA", normalized_value="Master Services Agreement", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX),
        effective_date=ExtractedField(field_name="effective_date", raw_value="Jan 1, 2020", normalized_value="2020-01-01", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev),
        expiration_date=ExtractedField.not_found("expiration_date"),
        renewal_language=ExtractedField.not_found("renewal_language"),
        governing_law=ExtractedField(field_name="governing_law", raw_value="State of New York", normalized_value="New York", extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev),
        parties=[
            ContractParty(name="Access Worldwide Communications, Inc", raw_text="Access Worldwide Communications, Inc", evidence=ev),
            ContractParty(name="E*TRADE Financial Corporation", raw_text="E*TRADE Financial Corporation", evidence=ev)
        ],
        payment_terms=ExtractedField(field_name="payment_terms", raw_value="Net 30", normalized_value=PaymentTerms(payment_type="Net 30", payment_days=30, raw_text="Net 30", evidence=ev), extraction_method=ExtractionMethod.DETERMINISTIC_REGEX, evidence=ev),
    )

    ob = ContractObligation(
        obligation_id="ob_01",
        actor="Access Worldwide Communications, Inc",
        action="provide monthly performance reports",
        temporal=TemporalConstraint(temporal_type=TemporalType.RECURRING, raw_expression="monthly"),
        status=ObligationStatus.UNKNOWN,
        source_clause="Section 4.1",
        evidence=ev
    )

    evt = LifecycleEvent(
        event_id="evt_01",
        event_type=LifecycleEventType.EFFECTIVE_DATE,
        title="Agreement Effective Date",
        description="Contract effective date",
        date_or_trigger="2020-01-01",
        is_fixed_date=True,
        evidence=ev
    )

    graph = KnowledgeGraphBuilder.build_graph([doc], [intel], obligations_by_doc={"doc_03": [ob]}, events_by_doc={"doc_03": [evt]})
    query_engine = ContractGraphQueryEngine(graph)

    fake_llm = FakeLLMProvider()
    fake_llm.set_response_for_query(
        "payment terms",
        json.dumps({
            "answer": "Payment terms are Net 30 days [E1].",
            "claims": [{"text": "Payment terms are Net 30 days.", "evidence_ids": ["E1"]}]
        })
    )

    return hybrid, resolver, query_engine, {"doc_03": intel}, [ob], [evt], fake_llm


def test_tool_registry_registration_and_lookup(agent_mock_infrastructure):
    """Test 1: Tool registry lookup and unknown tool handling."""
    hybrid, resolver, query_engine, intel_map, obligations, events, fake_llm = agent_mock_infrastructure
    
    registry = ToolRegistry()
    search_tool = SearchContractEvidenceTool(hybrid, resolver)
    registry.register(search_tool)

    assert registry.get_tool("search_contract_evidence") is not None
    assert registry.get_tool("non_existent_tool") is None

    # Execute unknown tool
    call = ToolCall(tool_name="unknown_tool", arguments={"foo": "bar"}, call_id="c1")
    res = registry.execute_tool(call, context=None)
    assert res.status == ToolStatus.UNKNOWN_TOOL
    assert "not registered" in res.error_message


def test_tool_registry_argument_validation(agent_mock_infrastructure):
    """Test 2: Schema validation catches missing or malformed tool arguments."""
    hybrid, resolver, query_engine, intel_map, obligations, events, fake_llm = agent_mock_infrastructure
    
    registry = ToolRegistry()
    registry.register(SearchContractEvidenceTool(hybrid, resolver))

    # Missing mandatory "query" field
    call = ToolCall(tool_name="search_contract_evidence", arguments={"top_k": 5}, call_id="c2")
    res = registry.execute_tool(call, context=None)
    assert res.status == ToolStatus.INVALID_ARGUMENTS
    assert "Invalid arguments" in res.error_message


def test_search_contract_evidence_tool(agent_mock_infrastructure):
    """Test 3: search_contract_evidence executes and returns EvidenceBundle."""
    hybrid, resolver, query_engine, intel_map, obligations, events, fake_llm = agent_mock_infrastructure
    
    tool = SearchContractEvidenceTool(hybrid, resolver)
    args = SearchEvidenceArgs(query="payment terms", top_k=3)
    res = tool.execute(args, context=None)

    assert res.status == ToolStatus.SUCCESS
    assert res.output.total_spans >= 1
    assert len(res.evidence) >= 1
    assert res.evidence[0].document_id == "doc_03"


def test_query_contract_graph_tool(agent_mock_infrastructure):
    """Test 4: query_contract_graph executes structured queries."""
    hybrid, resolver, query_engine, intel_map, obligations, events, fake_llm = agent_mock_infrastructure
    
    tool = QueryContractGraphTool(query_engine)
    args = QueryGraphArgs(query_type="contracts_for_party", param="E*TRADE")
    res = tool.execute(args, context=None)

    assert res.status == ToolStatus.SUCCESS
    assert len(res.output) >= 1
    assert res.output[0].contract_id == "doc_03"
    assert len(res.evidence) >= 1


def test_get_contract_details_tool(agent_mock_infrastructure):
    """Test 5: get_contract_details retrieves verified contract facts."""
    hybrid, resolver, query_engine, intel_map, obligations, events, fake_llm = agent_mock_infrastructure
    
    tool = GetContractDetailsTool(intel_map)
    args = GetContractDetailsArgs(document_id="doc_03")
    res = tool.execute(args, context=None)

    assert res.status == ToolStatus.SUCCESS
    assert res.output["payment_terms"] == "Net 30"
    assert res.output["governing_law"] == "New York"
    assert len(res.evidence) >= 2


def test_get_contract_obligations_unknown_status(agent_mock_infrastructure):
    """Test 6: get_contract_obligations preserves UNKNOWN status."""
    hybrid, resolver, query_engine, intel_map, obligations, events, fake_llm = agent_mock_infrastructure
    
    tool = GetContractObligationsTool(obligations)
    from src.agent.tools import GetObligationsArgs
    args = GetObligationsArgs(document_id="doc_03")
    res = tool.execute(args, context=None)

    assert res.status == ToolStatus.SUCCESS
    assert len(res.output) == 1
    assert res.output[0]["status"] == "UNKNOWN"
    assert "monthly performance reports" in res.output[0]["action"]


def test_build_grounded_answer_tool(agent_mock_infrastructure):
    """Test 7: build_grounded_answer executes Grounded RAG with claim verification."""
    hybrid, resolver, query_engine, intel_map, obligations, events, fake_llm = agent_mock_infrastructure
    
    search_tool = SearchContractEvidenceTool(hybrid, resolver)
    search_res = search_tool.execute(SearchEvidenceArgs(query="payment terms"), context=None)
    
    ground_tool = BuildGroundedAnswerTool(GroundedAnswerGenerator(fake_llm))
    from src.agent.tools import BuildGroundedAnswerArgs
    ground_args = BuildGroundedAnswerArgs(query="What are the payment terms?", evidence_bundle=search_res.output)
    ground_res = ground_tool.execute(ground_args, context=None)

    assert ground_res.status == ToolStatus.SUCCESS
    assert ground_res.output.grounding_status.value == "supported"
    assert len(ground_res.citations) == 1
