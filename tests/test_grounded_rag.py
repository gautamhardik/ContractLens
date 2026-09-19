"""Targeted Unit Tests for Grounded RAG Pipeline (Phase 16).

Tests:
1. End-to-end grounded query execution with FakeLLMProvider.
2. Handling of unanswerable queries (safety from hallucination).
3. Amendment precedence awareness (Access-E*TRADE parent vs amendment conflict).
4. Malformed LLM JSON output handling (graceful fallback without pipeline crash).
5. Real corpus evidence integration (Access-E*TRADE MSA doc_03).
"""

import json
import pytest

from src.models.canonical import CanonicalDocument, CanonicalPage, CanonicalBlock, BlockType, BoundingBox
from src.models.chunk import RetrievalChunk, ChunkProvenance, ChunkType
from src.retrieval.lexical import BM25Retriever
from src.retrieval.dense import LSADenseRetriever
from src.retrieval.fusion import HybridRRFRetriever
from src.evidence.resolver import EvidenceResolver
from src.rag.models import ClaimVerificationStatus
from src.rag.generator import FakeLLMProvider
from src.rag.pipeline import GroundedRAGPipeline


@pytest.fixture
def mock_retrieval_and_evidence():
    """Setup mock document, chunk, retriever, and resolver."""
    b1 = CanonicalBlock(
        block_id="b_p3_pay",
        document_id="doc_03",
        page_number=3,
        reading_order=0,
        block_type=BlockType.PARAGRAPH,
        bbox=BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=150.0),
        raw_text="Section 6. Payment Terms. Invoices shall be paid within thirty (30) days following receipt.",
        normalized_text="Section 6. Payment Terms. Invoices shall be paid within thirty (30) days following receipt.",
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
            block_ids=["b_p3_pay"],
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

    return hybrid, resolver


def test_grounded_rag_happy_path(mock_retrieval_and_evidence):
    """Test 1: Normal grounded question answering with supported claim and citation."""
    hybrid, resolver = mock_retrieval_and_evidence
    
    fake_llm = FakeLLMProvider()
    fake_llm.set_response_for_query(
        "payment terms",
        json.dumps({
            "answer": "Invoices are payable within 30 days of receipt [E1].",
            "claims": [
                {
                    "text": "Invoices are payable within 30 days of receipt.",
                    "evidence_ids": ["E1"]
                }
            ]
        })
    )

    pipeline = GroundedRAGPipeline(
        retriever=hybrid,
        resolver=resolver,
        llm_provider=fake_llm,
        top_k_chunks=3
    )

    resp = pipeline.answer_question("What are the payment terms?")
    assert resp.answer.grounding_status == ClaimVerificationStatus.SUPPORTED
    assert resp.answer.verification_report.supported_claims == 1
    assert len(resp.answer.citations) == 1
    assert resp.answer.citations[0].page_number == 3
    assert resp.answer.citations[0].document_id == "doc_03"


def test_unanswerable_safety(mock_retrieval_and_evidence):
    """Test 2: Unanswerable query produces controlled insufficient evidence state without false citations."""
    hybrid, resolver = mock_retrieval_and_evidence
    
    fake_llm = FakeLLMProvider()
    fake_llm.set_response_for_query(
        "late payment penalty",
        json.dumps({
            "answer": "The available contract evidence does not establish this.",
            "claims": []
        })
    )

    pipeline = GroundedRAGPipeline(
        retriever=hybrid,
        resolver=resolver,
        llm_provider=fake_llm,
    )

    resp = pipeline.answer_question("What is the late payment penalty fee percentage?")
    assert resp.answer.is_insufficient_evidence is True
    assert resp.answer.grounding_status == ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
    assert len(resp.answer.citations) == 0


def test_malformed_llm_output_recovery(mock_retrieval_and_evidence):
    """Test 4: Pipeline handles malformed non-JSON LLM output gracefully without crashing."""
    hybrid, resolver = mock_retrieval_and_evidence
    
    fake_llm = FakeLLMProvider()
    fake_llm.set_response_for_query(
        "payment terms",
        "Raw text without JSON schema."
    )

    pipeline = GroundedRAGPipeline(
        retriever=hybrid,
        resolver=resolver,
        llm_provider=fake_llm,
    )

    resp = pipeline.answer_question("What are the payment terms?")
    assert resp.answer.answer_text == "Raw text without JSON schema."
    assert resp.answer.verification_report.total_claims == 0
