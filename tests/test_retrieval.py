"""Targeted Unit Tests for Retrieval Engines (Phase 13).

Tests:
1. Deterministic BM25 ranking and scoring.
2. Deterministic Dense LSA ranking and scoring.
3. Hybrid RRF ranking and scoring.
4. Top-K retrieval behavior and bounds.
5. 100% Provenance preservation (chunk_id, doc_id, pages, bboxes).
6. Document filtering behavior.
7. Empty query and empty corpus edge case handling.
8. Unanswerable benchmark evaluation safety.
9. Retrieval metric calculations (Recall@k, MRR, Containment).
"""

import pytest
from typing import List

from src.models.canonical import BoundingBox
from src.models.chunk import RetrievalChunk, ChunkProvenance, ChunkType
from src.retrieval.lexical import BM25Retriever
from src.retrieval.dense import LSADenseRetriever
from src.retrieval.fusion import HybridRRFRetriever
from src.retrieval.evaluation import (
    evaluate_retrieval_strategy,
    QuestionRetrievalResult,
    BenchmarkSummary,
)
from experiments.evaluation.benchmark_schema import (
    BenchmarkQuestion,
    QuestionCategory,
    ReasoningType,
    DifficultyLevel,
    ExpectedEvidence,
)


def create_sample_chunks() -> List[RetrievalChunk]:
    """Create deterministic mock chunks for unit testing."""
    c1 = RetrievalChunk(
        chunk_id="chk_001",
        document_id="doc_alpha",
        chunk_type=ChunkType.SECTION,
        text="Section 3. Payment Terms. Invoices shall be paid net 30 days following receipt.",
        char_count=80,
        token_estimate=20,
        provenance=ChunkProvenance(
            document_id="doc_alpha",
            filename="alpha.pdf",
            page_start=3,
            page_end=3,
            block_ids=["blk_1"],
            section_number="3.0",
            section_title="Payment Terms",
            bounding_boxes=[BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=150.0)]
        )
    )
    c2 = RetrievalChunk(
        chunk_id="chk_002",
        document_id="doc_alpha",
        chunk_type=ChunkType.SECTION,
        text="Section 4. Termination. Either party may terminate upon thirty (30) days prior written notice.",
        char_count=98,
        token_estimate=24,
        provenance=ChunkProvenance(
            document_id="doc_alpha",
            filename="alpha.pdf",
            page_start=4,
            page_end=4,
            block_ids=["blk_2"],
            section_number="4.0",
            section_title="Termination",
            bounding_boxes=[BoundingBox(x0=50.0, y0=200.0, x1=500.0, y1=250.0)]
        )
    )
    c3 = RetrievalChunk(
        chunk_id="chk_003",
        document_id="doc_beta",
        chunk_type=ChunkType.SECTION,
        text="Governing Law. This Agreement shall be governed by the laws of the State of Delaware.",
        char_count=86,
        token_estimate=21,
        provenance=ChunkProvenance(
            document_id="doc_beta",
            filename="beta.pdf",
            page_start=12,
            page_end=12,
            block_ids=["blk_3"],
            section_number="12.1",
            section_title="Governing Law",
            bounding_boxes=[BoundingBox(x0=60.0, y0=300.0, x1=520.0, y1=350.0)]
        )
    )
    return [c1, c2, c3]


def test_bm25_deterministic_retrieval():
    chunks = create_sample_chunks()
    retriever = BM25Retriever(chunks)
    
    # Query matching payment terms ("days" also appears in chk_002, so chk_001 must rank first)
    res = retriever.retrieve("payment net 30 days", top_k=2)
    assert len(res) == 2
    assert res[0][0].chunk_id == "chk_001"
    assert res[0][1] > res[1][1]

    # Repeat query and assert exact deterministic scores
    res2 = retriever.retrieve("payment net 30 days", top_k=2)
    assert res[0][0].chunk_id == res2[0][0].chunk_id
    assert res[0][1] == res2[0][1]


def test_dense_lsa_deterministic_retrieval():
    chunks = create_sample_chunks()
    retriever = LSADenseRetriever(n_components=2, random_state=42)
    retriever.index(chunks)

    res = retriever.retrieve("Delaware laws governing", top_k=1)
    assert len(res) == 1
    assert res[0][0].chunk_id == "chk_003"
    assert 0.0 <= res[0][1] <= 1.0001


def test_hybrid_rrf_retrieval():
    chunks = create_sample_chunks()
    bm25 = BM25Retriever(chunks)
    dense = LSADenseRetriever(n_components=2, random_state=42)
    dense.index(chunks)

    hybrid = HybridRRFRetriever(bm25, dense, rrf_k=60)
    res = hybrid.retrieve("termination written notice", top_k=2)
    
    assert len(res) >= 1
    top_chunk, score = res[0]
    assert top_chunk.chunk_id == "chk_002"
    assert score > 0.0


def test_document_filtering():
    chunks = create_sample_chunks()
    bm25 = BM25Retriever(chunks)
    
    # Query without filter matches doc_beta
    res_all = bm25.retrieve("laws", top_k=5)
    assert any(c.document_id == "doc_beta" for c, _ in res_all)
    
    # Query filtering only doc_alpha must exclude doc_beta
    res_filtered = bm25.retrieve("laws", top_k=5, filter_doc_ids=["doc_alpha"])
    for c, _ in res_filtered:
        assert c.document_id == "doc_alpha"


def test_provenance_preservation():
    chunks = create_sample_chunks()
    bm25 = BM25Retriever(chunks)
    res = bm25.retrieve("net 30 days", top_k=1)
    
    chunk, _ = res[0]
    prov = chunk.provenance
    assert prov.document_id == "doc_alpha"
    assert prov.page_start == 3
    assert prov.page_end == 3
    assert prov.section_number == "3.0"
    assert prov.section_title == "Payment Terms"
    assert len(prov.bounding_boxes) == 1
    assert prov.bounding_boxes[0].x0 == 50.0


def test_empty_edge_cases():
    chunks = create_sample_chunks()
    bm25 = BM25Retriever(chunks)
    
    # Empty query
    assert bm25.retrieve("", top_k=5) == []
    assert bm25.retrieve("   ", top_k=5) == []
    
    # Empty retriever
    empty_bm25 = BM25Retriever([])
    assert empty_bm25.retrieve("test", top_k=5) == []


def test_retrieval_evaluation_metrics():
    chunks = create_sample_chunks()
    bm25 = BM25Retriever(chunks)
    
    q_ans = BenchmarkQuestion(
        question_id="Q_TEST_1",
        category=QuestionCategory.PAYMENT,
        reasoning_type=ReasoningType.DIRECT_LOOKUP,
        difficulty=DifficultyLevel.EASY,
        target_documents=["doc_alpha"],
        question="What are the payment terms?",
        expected_answer="Net 30 days",
        is_answerable=True,
        evidence_requirements=[
            ExpectedEvidence(
                document_id="doc_alpha",
                target_pages=[3],
                key_phrases=["net 30 days"]
            )
        ]
    )
    
    q_unans = BenchmarkQuestion(
        question_id="Q_TEST_2",
        category=QuestionCategory.PAYMENT,
        reasoning_type=ReasoningType.UNANSWERABLE,
        difficulty=DifficultyLevel.HARD,
        target_documents=["doc_alpha"],
        question="What is the late payment fee percentage?",
        expected_answer="Insufficient evidence.",
        is_answerable=False,
        unanswerable_reason="No late fee clause",
        evidence_requirements=[]
    )
    
    summary = evaluate_retrieval_strategy(
        strategy_name="BM25_Test",
        retriever_fn=bm25.retrieve,
        questions=[q_ans, q_unans],
        top_k=3,
        filter_by_target_docs=True
    )
    
    assert summary.answerable_count == 1
    assert summary.unanswerable_count == 1
    assert summary.recall_at_3 == 1.0
    assert summary.mrr == 1.0
    assert summary.evidence_containment_rate == 1.0
    assert summary.provenance_correctness_rate == 1.0
    assert summary.unanswerable_safe_rate == 1.0
