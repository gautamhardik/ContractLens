"""Focused Unit and Regression Tests for Evaluation Dataset & Chunking Engines (Phase 10–12).

Validates:
1. Golden Benchmark dataset integrity (40 questions, 8 categories, 5 questions/category).
2. Evidence requirement completeness (document_id, target_pages, key_phrases).
3. Answerability and unanswerability flags (5 unanswerable questions with reasons).
4. Chunking abstractions: BaseChunker, FixedSlidingWindowChunker, SectionAwareChunker.
5. 100% Provenance preservation in RetrievalChunks (page range, block_ids, bboxes, section metadata).
6. Cross-page clause handling and dedicated table chunking.
"""

import os
import re
import pytest

from experiments.evaluation.benchmark_dataset import get_evaluation_dataset
from experiments.evaluation.benchmark_schema import QuestionCategory, ReasoningType
from src.ingestion.reconstructor import StructuralReconstructor
from src.retrieval.chunking import FixedSlidingWindowChunker, SectionAwareChunker
from src.models.chunk import ChunkType, RetrievalChunk


RAW_DIR = r"c:\Users\hiten\Downloads\ContractLens\Data\raw"


def get_raw_path(needle: str) -> str:
    needle_clean = re.sub(r'[^a-zA-Z0-9]', '', needle).lower()
    for f in os.listdir(RAW_DIR):
        f_clean = re.sub(r'[^a-zA-Z0-9]', '', f).lower()
        if needle_clean in f_clean:
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(f"File matching '{needle}' not found in {RAW_DIR}")


def test_benchmark_dataset_integrity():
    """Verify 40 questions across exactly 8 categories with 5 questions per category."""
    questions = get_evaluation_dataset()
    assert len(questions) == 40

    from collections import Counter
    cat_counts = Counter(q.category for q in questions)
    assert len(cat_counts) == 8
    for cat, count in cat_counts.items():
        assert count == 5, f"Category {cat} does not have exactly 5 questions (has {count})"

    # Verify unanswerable questions
    unanswerable = [q for q in questions if not q.is_answerable]
    assert len(unanswerable) == 7, f"Expected 7 unanswerable questions, got {len(unanswerable)}"
    for u in unanswerable:
        assert u.unanswerable_reason is not None
        assert "insufficient evidence" in u.expected_answer.lower() or "no" in u.expected_answer.lower()

    # Verify every question has evidence requirements
    for q in questions:
        assert len(q.evidence_requirements) > 0
        for req in q.evidence_requirements:
            assert req.document_id.startswith("doc_")
            assert len(req.target_pages) > 0
            assert len(req.key_phrases) > 0


def test_sliding_window_chunker_provenance():
    """Verify FixedSlidingWindowChunker preserves 100% provenance and block linkage."""
    path = get_raw_path("Access-E-TRADE MSA")
    doc = StructuralReconstructor().reconstruct_document(path, "doc_03")

    chunker = FixedSlidingWindowChunker(target_chars=1000, overlap_chars=200)
    chunks = chunker.chunk(doc)

    assert len(chunks) > 0
    for c in chunks:
        assert c.chunk_type == ChunkType.SLIDING_WINDOW
        assert len(c.text) > 0
        assert c.char_count == len(c.text)
        assert c.token_estimate > 0
        # Provenance guarantees
        assert c.provenance.document_id == "doc_03"
        assert c.provenance.page_start >= 1
        assert c.provenance.page_end >= c.provenance.page_start
        assert len(c.provenance.block_ids) > 0
        assert len(c.provenance.bounding_boxes) == len(c.provenance.block_ids)
        ev_ref = c.provenance.to_evidence_ref()
        assert ev_ref.document_id == "doc_03"
        assert ev_ref.page_number == c.provenance.page_start


def test_section_aware_chunker_structural_hierarchy():
    """Verify SectionAwareChunker respects section boundaries and captures tables."""
    path = get_raw_path("Access-E-TRADE MSA")
    doc = StructuralReconstructor().reconstruct_document(path, "doc_03")

    chunker = SectionAwareChunker(max_chars=2500, min_chars=150)
    chunks = chunker.chunk(doc)

    assert len(chunks) > 0
    # Check that sections are identified
    section_chunks = [c for c in chunks if c.chunk_type == ChunkType.SECTION]
    assert len(section_chunks) > 0

    # Test on Square-Marqeta (contains financial fee tables)
    marqeta_path = get_raw_path("Square-Marqeta")
    marqeta_doc = StructuralReconstructor().reconstruct_document(marqeta_path, "doc_16")
    marqeta_chunks = chunker.chunk(marqeta_doc)

    table_chunks = [c for c in marqeta_chunks if c.chunk_type == ChunkType.TABLE]
    assert len(table_chunks) > 0
    assert table_chunks[0].provenance.document_id == "doc_16"
    assert table_chunks[0].provenance.section_title is not None


def test_cross_page_clause_continuity():
    """Verify that multi-block and cross-page sections are properly bounded."""
    path = get_raw_path("Access-E-TRADE MSA")
    doc = StructuralReconstructor().reconstruct_document(path, "doc_03")

    chunker = SectionAwareChunker(max_chars=2500, min_chars=150)
    chunks = chunker.chunk(doc)

    # Cross-page chunks should retain both page_start and page_end
    cross_page = [c for c in chunks if c.provenance.page_start != c.provenance.page_end]
    assert len(cross_page) > 0
    for cp in cross_page:
        assert cp.metadata["is_cross_page"] is True
        assert cp.provenance.page_end > cp.provenance.page_start
