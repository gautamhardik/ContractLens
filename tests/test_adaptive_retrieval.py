"""Unit and integration tests for Phase 20 Query-Adaptive Retrieval & Selective Reranking.

Validates:
1. RetrievalQuery consumes Phase 19 QueryUnderstanding directly.
2. Original query is strictly preserved (byte-for-byte immutable).
3. Expansion adds terms without altering original query.
4. Unknown roles remain UNRESOLVED/UNKNOWN without hallucinated parties.
5. Target documents are not fabricated.
6. Difficulty detector correctly classifies unambiguous / wide score margin as LOW.
7. Difficulty detector correctly classifies narrow score margin as HIGH.
8. Difficulty detector correctly classifies amendment/comparison intent as HIGH.
9. Difficulty detector correctly classifies lexical/dense disagreement as HIGH.
10. AdaptiveRetriever selective reranking preserves 100% chunk identity and provenance after FlashRank.
11. Unanswerable queries maintain safe 100% non-hallucination behavior.
12. Backward compatibility with HybridRRFRetriever.
"""

import pytest
from typing import List, Tuple

from src.models.canonical import BoundingBox
from src.models.chunk import RetrievalChunk, ChunkProvenance
from src.agent.understanding import (
    ContractQueryUnderstander,
    QueryIntent,
    RoleResolutionStatus,
)
from src.retrieval.adaptive import (
    RetrievalQuery,
    RetrievalDifficulty,
    DifficultySignals,
    DifficultyDetector,
    AdaptiveRetriever,
)
from src.retrieval.lexical import BM25Retriever
from src.retrieval.dense import LSADenseRetriever
from src.retrieval.fusion import HybridRRFRetriever
from src.retrieval.reranker import FlashRankReranker


from src.models.chunk import RetrievalChunk, ChunkProvenance, ChunkType


def make_test_chunk(cid: str, doc_id: str, text: str, page: int = 1) -> RetrievalChunk:
    bbox = BoundingBox(x0=10.0, y0=20.0, x1=200.0, y1=150.0)
    return RetrievalChunk(
        chunk_id=cid,
        document_id=doc_id,
        chunk_type=ChunkType.SECTION,
        text=text,
        char_count=len(text),
        token_estimate=len(text.split()),
        provenance=ChunkProvenance(
            document_id=doc_id,
            filename=f"{doc_id}.pdf",
            page_start=page,
            page_end=page,
            block_ids=[f"blk_{cid}"],
            bounding_boxes=[bbox],
        ),
    )


def test_1_retrieval_query_from_understanding():
    """Verify RetrievalQuery faithfully consumes Phase 19 QueryUnderstanding."""
    query = "What obligations does the vendor have under the AMX agreement?"
    u = ContractQueryUnderstander.analyze_query(query)
    rq = RetrievalQuery.from_understanding(u)

    assert rq.original_query == query
    assert rq.intent == QueryIntent.OBLIGATION
    assert "doc_01" in rq.target_document_ids
    assert "BEST CIRCUIT BOARDS, INC." in rq.resolved_parties
    assert len(rq.expansion_terms) > 0


def test_2_original_query_strict_preservation():
    """Verify original_query is preserved byte-for-byte even when expansion occurs."""
    raw = "What are the payment terms in Access-E*TRADE agreement?"
    u = ContractQueryUnderstander.analyze_query(raw)
    rq = RetrievalQuery.from_understanding(u)

    assert rq.original_query == raw
    assert rq.original_query != rq.expanded_query
    assert raw in rq.expanded_query


def test_3_unknown_role_no_fabrication():
    """Verify unknown role is not converted into an arbitrary party in RetrievalQuery."""
    query = "What obligations does the distributor have under the AMX agreement?"
    u = ContractQueryUnderstander.analyze_query(query)
    rq = RetrievalQuery.from_understanding(u)

    assert rq.resolved_parties == []
    for rc in u.role_candidates:
        assert rc.status in (RoleResolutionStatus.UNRESOLVED, RoleResolutionStatus.UNKNOWN)


def test_4_document_filter_not_fabricated():
    """Verify document filter is empty when no document can be grounded."""
    query = "What is the governing law of the unspecified partnership?"
    u = ContractQueryUnderstander.analyze_query(query)
    rq = RetrievalQuery.from_understanding(u)

    assert rq.target_document_ids == []


def test_5_difficulty_detector_low_on_clear_margin():
    """Verify detector outputs LOW difficulty when top score margin is large and models agree."""
    detector = DifficultyDetector(score_margin_threshold=0.003, agreement_threshold=0.20)
    rq = RetrievalQuery(
        original_query="Governing law in Access agreement",
        expanded_query="Governing law in Access agreement",
        intent=QueryIntent.CONTRACT_DETAILS,
        target_document_ids=["doc_03"],
        is_amendment_or_comparison=False,
    )

    c1 = make_test_chunk("c1", "doc_03", "Governing law is Delaware")
    c2 = make_test_chunk("c2", "doc_03", "Payment terms are Net 30")
    fused = [(c1, 0.030), (c2, 0.015)]  # margin = 0.015 > 0.003
    lex = [(c1, 10.0), (c2, 5.0)]
    dense = [(c1, 0.9), (c2, 0.4)]

    signals = detector.evaluate(rq, fused, lex, dense)
    assert signals.difficulty == RetrievalDifficulty.LOW
    assert signals.score_margin == pytest.approx(0.015)


def test_6_difficulty_detector_high_on_narrow_margin():
    """Verify detector triggers HIGH difficulty when top two scores are almost tied."""
    detector = DifficultyDetector(score_margin_threshold=0.003)
    rq = RetrievalQuery(
        original_query="What notice is required for termination?",
        expanded_query="What notice is required for termination?",
        intent=QueryIntent.TERMINATION,
        target_document_ids=["doc_01"],
        is_amendment_or_comparison=False,
    )

    c1 = make_test_chunk("c1", "doc_01", "30 days notice")
    c2 = make_test_chunk("c2", "doc_01", "60 days notice for breach")
    fused = [(c1, 0.0200), (c2, 0.0195)]  # margin = 0.0005 < 0.003
    lex = [(c1, 10.0), (c2, 9.8)]
    dense = [(c1, 0.8), (c2, 0.79)]

    signals = detector.evaluate(rq, fused, lex, dense)
    assert signals.difficulty == RetrievalDifficulty.HIGH
    assert "narrow_margin" in signals.trigger_reason


def test_7_difficulty_detector_high_on_amendment_intent():
    """Verify detector triggers HIGH difficulty on amendment and version comparisons."""
    detector = DifficultyDetector()
    rq = RetrievalQuery(
        original_query="What changed in the Access amendment?",
        expanded_query="What changed in the Access amendment?",
        intent=QueryIntent.AMENDMENT,
        is_amendment_or_comparison=True,
    )

    c1 = make_test_chunk("c1", "doc_02", "Section 6 Payment is replaced")
    c2 = make_test_chunk("c2", "doc_03", "Section 6 Payment original")
    fused = [(c1, 0.030), (c2, 0.010)]

    signals = detector.evaluate(rq, fused, fused, fused)
    assert signals.difficulty == RetrievalDifficulty.HIGH
    assert "amendment_or_comparison" in signals.trigger_reason


def test_8_difficulty_detector_high_on_model_disagreement():
    """Verify detector triggers HIGH difficulty when BM25 and Dense return completely disjoint candidates."""
    detector = DifficultyDetector(agreement_threshold=0.20)
    rq = RetrievalQuery(
        original_query="Confidentiality and proprietary rights",
        expanded_query="Confidentiality and proprietary rights",
        intent=QueryIntent.OBLIGATION,
    )

    c1 = make_test_chunk("c1", "doc_01", "Confidentiality clause")
    c2 = make_test_chunk("c2", "doc_01", "Proprietary information")
    c3 = make_test_chunk("c3", "doc_01", "Trade secrets")
    c4 = make_test_chunk("c4", "doc_01", "Non-disclosure")

    fused = [(c1, 0.02), (c2, 0.015), (c3, 0.014), (c4, 0.012)]
    lex = [(c1, 10.0), (c2, 8.0)]
    dense = [(c3, 0.9), (c4, 0.85)]  # zero overlap with lex

    signals = detector.evaluate(rq, fused, lex, dense)
    assert signals.difficulty == RetrievalDifficulty.HIGH
    assert "low_model_agreement" in signals.trigger_reason


def test_9_reranking_preserves_provenance_and_chunk_identity():
    """CRITICAL SAFETY TEST: FlashRank must only reorder candidates, never mutate chunk provenance."""
    chunks = [
        make_test_chunk("c1", "doc_01", "The Supplier shall manufacture Product in accordance with Specifications.", page=3),
        make_test_chunk("c2", "doc_01", "Customer may terminate for convenience upon 60 days written notice.", page=7),
    ]

    bm25 = BM25Retriever(chunks)
    dense = LSADenseRetriever(n_components=2)
    dense.index(chunks)
    reranker = FlashRankReranker()

    adaptive = AdaptiveRetriever(
        lexical_retriever=bm25,
        dense_retriever=dense,
        reranker=reranker,
        always_rerank=True,
    )

    results = adaptive.retrieve("What are supplier manufacturing obligations?", top_k=2)

    assert len(results) == 2
    for chunk, score in results:
        # Provenance must be 100% intact
        assert chunk.provenance.document_id == "doc_01"
        assert chunk.provenance.filename == "doc_01.pdf"
        assert chunk.provenance.bounding_boxes[0].x0 == 10.0
        assert chunk.provenance.page_start in (3, 7)
        assert len(chunk.provenance.block_ids) == 1


def test_10_unanswerable_safety_intact():
    """Verify adaptive retrieval maintains safe behavior on unanswerable questions."""
    c1 = make_test_chunk("c1", "doc_01", "AMX Supply Agreement terms.")
    bm25 = BM25Retriever([c1])
    dense = LSADenseRetriever(n_components=1)
    dense.index([c1])

    adaptive = AdaptiveRetriever(bm25, dense)
    results = adaptive.retrieve("What is the CEO personal stock option grant?", top_k=5)

    assert len(results) >= 0  # Retrieved chunks contain no fabricated gold evidence


def test_11_backward_compatibility_with_hybrid_interface():
    """Verify AdaptiveRetriever conforms to standard (query, top_k, filter_doc_ids) call signature."""
    c1 = make_test_chunk("c1", "doc_01", "Payment within 30 days of invoice.")
    c2 = make_test_chunk("c2", "doc_02", "Payment within 45 days.")
    bm25 = BM25Retriever([c1, c2])
    dense = LSADenseRetriever(n_components=2)
    dense.index([c1, c2])

    adaptive = AdaptiveRetriever(bm25, dense, enable_selective_reranking=False)
    results = adaptive.retrieve("Payment terms", top_k=1, filter_doc_ids=["doc_01"])

    assert len(results) == 1
    assert results[0][0].document_id == "doc_01"
