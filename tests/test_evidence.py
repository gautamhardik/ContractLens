"""Comprehensive Targeted Unit Tests for Evidence Layer (Phase 15).

Tests:
1. Valid resolution of known chunk to CanonicalDocument, page, block, raw text, and bbox.
2. Invalid document ID fails explicitly (ValidationStatus.INVALID_DOCUMENT).
3. Invalid block ID fails explicitly (ValidationStatus.INVALID_BLOCK).
4. Page/block mismatch detection (ValidationStatus.INCONSISTENT_PROVENANCE).
5. Invalid/malformed bounding box rejection (ValidationStatus.INVALID_BBOX).
6. Citation integrity: valid reference produces valid citation with 100% provenance retention.
7. Multi-block chunk resolves deterministically into ordered EvidenceSpans.
8. Deduplication: repeated references to the same canonical block are merged without losing retrieval pointers.
9. Deterministic ordering: identical inputs produce strictly identical EvidenceBundle sequence.
10. Missing provenance produces explicit failure rather than fabricated evidence.
11. Real corpus ground truth verification on Access-E*TRADE MSA (doc_03) and Amendment (doc_04).
12. Table evidence verification on table-dense contract.
"""

import os
import re
import pytest
from typing import List

from src.models.canonical import (
    BlockType,
    BoundingBox,
    CanonicalBlock,
    CanonicalPage,
    CanonicalDocument,
    TableData,
    TableRow,
    TableCell,
)
from src.models.chunk import RetrievalChunk, ChunkProvenance, ChunkType
from src.evidence.models import (
    ValidationStatus,
    EvidenceSpan,
    EvidenceCitation,
    EvidenceValidation,
    EvidenceBundle,
)
from src.evidence.validator import EvidenceValidator
from src.evidence.resolver import EvidenceResolver
from src.ingestion.reconstructor import StructuralReconstructor

RAW_DIR = r"c:\Users\hiten\Downloads\ContractLens\Data\raw"


def get_raw_path(needle: str) -> str:
    """Find file in Data/raw by alphanumeric substring match."""
    needle_clean = re.sub(r'[^a-zA-Z0-9]', '', needle).lower()
    for f in os.listdir(RAW_DIR):
        f_clean = re.sub(r'[^a-zA-Z0-9]', '', f).lower()
        if needle_clean in f_clean:
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(f"File matching '{needle}' not found in {RAW_DIR}")


@pytest.fixture
def mock_canonical_doc() -> CanonicalDocument:
    """Fixture providing a deterministic two-page CanonicalDocument."""
    b1 = CanonicalBlock(
        block_id="b_p1_01",
        document_id="doc_mock",
        page_number=1,
        reading_order=0,
        block_type=BlockType.HEADING,
        bbox=BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=80.0),
        raw_text="SECTION 1. DEFINITIONS",
        normalized_text="SECTION 1. DEFINITIONS",
        section_number="1",
        section_title="DEFINITIONS",
    )
    b2 = CanonicalBlock(
        block_id="b_p1_02",
        document_id="doc_mock",
        page_number=1,
        reading_order=1,
        block_type=BlockType.PARAGRAPH,
        bbox=BoundingBox(x0=50.0, y0=90.0, x1=500.0, y1=150.0),
        raw_text="Agreement means this Master Services Agreement between Party A and Party B.",
        normalized_text="Agreement means this Master Services Agreement between Party A and Party B.",
        section_number="1.1",
        section_title="Agreement Definition",
    )
    p1 = CanonicalPage(page_number=1, width=612.0, height=792.0, blocks=[b1, b2])

    b3 = CanonicalBlock(
        block_id="b_p2_01",
        document_id="doc_mock",
        page_number=2,
        reading_order=0,
        block_type=BlockType.PARAGRAPH,
        bbox=BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=200.0),
        raw_text="SECTION 6. PAYMENT. Invoices shall be paid within thirty (30) days.",
        normalized_text="SECTION 6. PAYMENT. Invoices shall be paid within thirty (30) days.",
        section_number="6.0",
        section_title="PAYMENT",
    )
    p2 = CanonicalPage(page_number=2, width=612.0, height=792.0, blocks=[b3])

    return CanonicalDocument(
        document_id="doc_mock",
        filename="mock_agreement.pdf",
        file_size=1024,
        page_count=2,
        pages=[p1, p2],
    )


# =============================================================================
# TESTS 1 - 10: UNIT & ISOLATION TESTS
# =============================================================================

def test_1_valid_resolution(mock_canonical_doc):
    """Test 1: Known chunk resolves successfully to CanonicalDocument, page, block, raw text, and bbox."""
    resolver = EvidenceResolver([mock_canonical_doc])
    chunk = RetrievalChunk(
        chunk_id="chk_001",
        document_id="doc_mock",
        chunk_type=ChunkType.SECTION,
        text="SECTION 1. DEFINITIONS\n\nAgreement means this Master Services Agreement...",
        char_count=80,
        token_estimate=20,
        provenance=ChunkProvenance(
            document_id="doc_mock",
            filename="mock_agreement.pdf",
            page_start=1,
            page_end=1,
            block_ids=["b_p1_01", "b_p1_02"],
            bounding_boxes=[
                BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=80.0),
                BoundingBox(x0=50.0, y0=90.0, x1=500.0, y1=150.0),
            ]
        )
    )

    spans, citations, validations = resolver.resolve_chunk(chunk)
    assert len(spans) == 2
    assert len(citations) == 2
    assert len(validations) == 2
    assert all(v.is_valid for v in validations)

    assert spans[0].block_id == "b_p1_01"
    assert spans[0].raw_text == "SECTION 1. DEFINITIONS"
    assert spans[0].bbox.x0 == 50.0
    assert spans[1].block_id == "b_p1_02"
    assert "Party A and Party B" in spans[1].raw_text


def test_2_invalid_document(mock_canonical_doc):
    """Test 2: Unknown document_id must fail explicitly with INVALID_DOCUMENT."""
    resolver = EvidenceResolver([mock_canonical_doc])
    chunk = RetrievalChunk(
        chunk_id="chk_err_doc",
        document_id="doc_non_existent",
        chunk_type=ChunkType.SECTION,
        text="Unknown text",
        char_count=12,
        token_estimate=3,
        provenance=ChunkProvenance(
            document_id="doc_non_existent",
            filename="unknown.pdf",
            page_start=1,
            page_end=1,
            block_ids=["b_p1_01"],
            bounding_boxes=[BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=80.0)]
        )
    )

    spans, citations, validations = resolver.resolve_chunk(chunk)
    assert len(spans) == 0
    assert len(citations) == 1
    assert citations[0].is_valid is False
    assert citations[0].validation_status == ValidationStatus.INVALID_DOCUMENT
    assert validations[0].document_resolved is False


def test_3_invalid_block(mock_canonical_doc):
    """Test 3: Unknown block_id must fail explicitly with INVALID_BLOCK."""
    resolver = EvidenceResolver([mock_canonical_doc])
    chunk = RetrievalChunk(
        chunk_id="chk_err_blk",
        document_id="doc_mock",
        chunk_type=ChunkType.SECTION,
        text="Unknown block text",
        char_count=18,
        token_estimate=4,
        provenance=ChunkProvenance(
            document_id="doc_mock",
            filename="mock_agreement.pdf",
            page_start=1,
            page_end=1,
            block_ids=["b_ghost_block"],
            bounding_boxes=[BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=80.0)]
        )
    )

    spans, citations, validations = resolver.resolve_chunk(chunk)
    assert len(spans) == 0
    assert len(citations) == 1
    assert citations[0].is_valid is False
    assert citations[0].validation_status == ValidationStatus.INVALID_BLOCK
    assert validations[0].block_resolved is False


def test_4_page_block_mismatch(mock_canonical_doc):
    """Test 4: Block belonging to another page must trigger INCONSISTENT_PROVENANCE."""
    val = EvidenceValidator.validate_block_reference(
        doc=mock_canonical_doc,
        document_id="doc_mock",
        page_number=1,  # Claimed page 1
        block_id="b_p2_01",  # But b_p2_01 is on page 2!
        bbox=BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=200.0),
    )

    assert val.is_valid is False
    assert val.status == ValidationStatus.INCONSISTENT_PROVENANCE
    assert any("belongs to page 2" in r for r in val.failure_reasons)


def test_5_invalid_bbox():
    """Test 5: Malformed or negative/inverted bbox must be rejected."""
    inverted_bbox = BoundingBox(x0=200.0, y0=50.0, x1=100.0, y1=80.0)  # x0 > x1
    is_ok, err = EvidenceValidator.validate_bounding_box(inverted_bbox, page_width=612.0, page_height=792.0)
    assert is_ok is False
    assert "x0 (200.0) > x1 (100.0)" in err

    neg_bbox = BoundingBox(x0=-10.0, y0=50.0, x1=100.0, y1=80.0)
    is_ok2, err2 = EvidenceValidator.validate_bounding_box(neg_bbox, page_width=612.0, page_height=792.0)
    assert is_ok2 is False
    assert "negative coordinates" in err2


def test_6_citation_integrity(mock_canonical_doc):
    """Test 6: Valid reference produces valid citation preserving 100% provenance."""
    resolver = EvidenceResolver([mock_canonical_doc])
    chunk = RetrievalChunk(
        chunk_id="chk_p2",
        document_id="doc_mock",
        chunk_type=ChunkType.SECTION,
        text="SECTION 6. PAYMENT.",
        char_count=19,
        token_estimate=5,
        provenance=ChunkProvenance(
            document_id="doc_mock",
            filename="mock_agreement.pdf",
            page_start=2,
            page_end=2,
            block_ids=["b_p2_01"],
            section_number="6.0",
            section_title="PAYMENT",
            bounding_boxes=[BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=200.0)]
        )
    )

    spans, citations, validations = resolver.resolve_chunk(chunk)
    assert len(citations) == 1
    cit = citations[0]
    assert cit.is_valid is True
    assert cit.validation_status == ValidationStatus.VALID
    assert cit.document_id == "doc_mock"
    assert cit.page_number == 2
    assert cit.block_id == "b_p2_01"
    assert cit.section_number == "6.0"
    assert cit.source_chunk_id == "chk_p2"


def test_7_multiple_blocks_in_chunk(mock_canonical_doc):
    """Test 7: A chunk spanning multiple canonical blocks resolves deterministically."""
    resolver = EvidenceResolver([mock_canonical_doc])
    chunk = RetrievalChunk(
        chunk_id="chk_multi",
        document_id="doc_mock",
        chunk_type=ChunkType.SECTION,
        text="Full section text...",
        char_count=100,
        token_estimate=25,
        provenance=ChunkProvenance(
            document_id="doc_mock",
            filename="mock_agreement.pdf",
            page_start=1,
            page_end=2,
            block_ids=["b_p1_01", "b_p1_02", "b_p2_01"],
            bounding_boxes=[
                BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=80.0),
                BoundingBox(x0=50.0, y0=90.0, x1=500.0, y1=150.0),
                BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=200.0),
            ]
        )
    )

    bundle = resolver.create_evidence_bundle(query="What are the terms?", retrieved_chunks=[chunk])
    assert bundle.is_fully_valid is True
    assert len(bundle.evidence_spans) == 3
    assert [s.block_id for s in bundle.evidence_spans] == ["b_p1_01", "b_p1_02", "b_p2_01"]


def test_8_deduplication(mock_canonical_doc):
    """Test 8: Repeated references to the same canonical block are deduplicated while retaining retrieval provenance."""
    resolver = EvidenceResolver([mock_canonical_doc])
    # Chunk A references b_p1_01 and b_p1_02
    chunk_a = RetrievalChunk(
        chunk_id="chk_A",
        document_id="doc_mock",
        chunk_type=ChunkType.SECTION,
        text="Chunk A",
        char_count=10,
        token_estimate=2,
        provenance=ChunkProvenance(
            document_id="doc_mock",
            filename="mock_agreement.pdf",
            page_start=1,
            page_end=1,
            block_ids=["b_p1_01", "b_p1_02"],
            bounding_boxes=[
                BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=80.0),
                BoundingBox(x0=50.0, y0=90.0, x1=500.0, y1=150.0),
            ]
        )
    )
    # Chunk B also references b_p1_02 (overlap)
    chunk_b = RetrievalChunk(
        chunk_id="chk_B",
        document_id="doc_mock",
        chunk_type=ChunkType.SECTION,
        text="Chunk B",
        char_count=10,
        token_estimate=2,
        provenance=ChunkProvenance(
            document_id="doc_mock",
            filename="mock_agreement.pdf",
            page_start=1,
            page_end=1,
            block_ids=["b_p1_02"],
            bounding_boxes=[BoundingBox(x0=50.0, y0=90.0, x1=500.0, y1=150.0)]
        )
    )

    bundle = resolver.create_evidence_bundle(query="Test overlap", retrieved_chunks=[chunk_a, chunk_b])
    # There are 3 total raw block references across both chunks, but only 2 unique canonical blocks
    assert len(bundle.citations) == 3
    assert len(bundle.evidence_spans) == 2

    # b_p1_02 should record linkage to BOTH chunk_A and chunk_B
    span_b2 = next(s for s in bundle.evidence_spans if s.block_id == "b_p1_02")
    assert sorted(span_b2.metadata["source_chunk_ids"]) == ["chk_A", "chk_B"]


def test_9_deterministic_ordering(mock_canonical_doc):
    """Test 9: Identical input twice produces identical EvidenceBundle sequence."""
    resolver = EvidenceResolver([mock_canonical_doc])
    chunk_1 = RetrievalChunk(
        chunk_id="chk_1",
        document_id="doc_mock",
        chunk_type=ChunkType.SECTION,
        text="Text",
        char_count=4,
        token_estimate=1,
        provenance=ChunkProvenance(
            document_id="doc_mock",
            filename="mock_agreement.pdf",
            page_start=2,
            page_end=2,
            block_ids=["b_p2_01"],
            bounding_boxes=[BoundingBox(x0=50.0, y0=100.0, x1=500.0, y1=200.0)]
        )
    )
    chunk_2 = RetrievalChunk(
        chunk_id="chk_2",
        document_id="doc_mock",
        chunk_type=ChunkType.SECTION,
        text="Text",
        char_count=4,
        token_estimate=1,
        provenance=ChunkProvenance(
            document_id="doc_mock",
            filename="mock_agreement.pdf",
            page_start=1,
            page_end=1,
            block_ids=["b_p1_01"],
            bounding_boxes=[BoundingBox(x0=50.0, y0=50.0, x1=500.0, y1=80.0)]
        )
    )

    bundle_1 = resolver.create_evidence_bundle("query", [chunk_1, chunk_2])
    bundle_2 = resolver.create_evidence_bundle("query", [chunk_1, chunk_2])

    order_1 = [(s.document_id, s.page_number, s.block_id) for s in bundle_1.evidence_spans]
    order_2 = [(s.document_id, s.page_number, s.block_id) for s in bundle_2.evidence_spans]

    assert order_1 == order_2
    # Also verify that page 1 comes before page 2 despite chunk_1 being passed first
    assert order_1 == [("doc_mock", 1, "b_p1_01"), ("doc_mock", 2, "b_p2_01")]


def test_10_missing_provenance():
    """Test 10: Missing provenance produces explicit failure rather than fabricated evidence."""
    resolver = EvidenceResolver([])
    chunk_empty = RetrievalChunk(
        chunk_id="chk_empty",
        document_id="doc_mock",
        chunk_type=ChunkType.SECTION,
        text="No provenance",
        char_count=13,
        token_estimate=3,
        provenance=ChunkProvenance(
            document_id="doc_mock",
            filename="mock.pdf",
            page_start=1,
            page_end=1,
            block_ids=[],  # Empty blocks!
            bounding_boxes=[]
        )
    )

    spans, citations, validations = resolver.resolve_chunk(chunk_empty)
    assert len(spans) == 0
    assert len(validations) == 1
    assert validations[0].status == ValidationStatus.MISSING_PROVENANCE
    assert validations[0].is_valid is False


# =============================================================================
# TESTS 11 & 12: REAL CORPUS GROUND TRUTH & TABLE TESTS
# =============================================================================

def test_11_real_corpus_access_etrade_resolution():
    """Test 11: Real corpus ground truth verification on Access-E*TRADE MSA (doc_03)."""
    # Specifically match MSA to avoid matching Amendment (doc_02)
    pdf_path = get_raw_path("AccessETRADEMSA")
    reconstructor = StructuralReconstructor()
    doc = reconstructor.reconstruct_document(pdf_path, "doc_03")

    resolver = EvidenceResolver([doc])

    # Find the block containing the governing law clause (Section 18.4, Page 12)
    p12 = next(p for p in doc.pages if p.page_number == 12)
    law_block = next(b for b in p12.blocks if "laws of the State of Delaware" in b.raw_text)

    # Create a synthetic chunk representing retrieved evidence
    chunk = RetrievalChunk(
        chunk_id="chk_real_access_law",
        document_id="doc_03",
        chunk_type=ChunkType.SECTION,
        text=law_block.raw_text,
        char_count=len(law_block.raw_text),
        token_estimate=len(law_block.raw_text) // 4,
        provenance=ChunkProvenance(
            document_id="doc_03",
            filename=doc.filename,
            page_start=12,
            page_end=12,
            block_ids=[law_block.block_id],
            section_number=law_block.section_number,
            section_title=law_block.section_title,
            bounding_boxes=[law_block.bbox]
        )
    )

    bundle = resolver.create_evidence_bundle("Governing law?", [chunk])
    assert bundle.is_fully_valid is True
    assert len(bundle.evidence_spans) == 1
    span = bundle.evidence_spans[0]
    assert span.document_id == "doc_03"
    assert span.page_number == 12
    assert span.block_id == law_block.block_id
    assert "laws of the State of Delaware" in span.raw_text
    assert span.bbox.x0 > 0 and span.bbox.y0 > 0
    assert span.bbox.x1 <= p12.width + 10.0


def test_12_table_evidence_verification():
    """Test 12: Verify table block provenance on real table-dense contract (Square-Marqeta doc_12)."""
    pdf_path = get_raw_path("Square")
    reconstructor = StructuralReconstructor()
    doc = reconstructor.reconstruct_document(pdf_path, "doc_12")

    resolver = EvidenceResolver([doc])

    # Find the first table block
    table_block = None
    table_page = None
    for p in doc.pages:
        for b in p.blocks:
            if b.block_type == BlockType.TABLE and b.table_data is not None:
                table_block = b
                table_page = p
                break
        if table_block:
            break

    assert table_block is not None
    assert table_page is not None

    chunk = RetrievalChunk(
        chunk_id="chk_table_test",
        document_id="doc_12",
        chunk_type=ChunkType.TABLE,
        text=table_block.raw_text,
        char_count=len(table_block.raw_text),
        token_estimate=len(table_block.raw_text) // 4,
        provenance=ChunkProvenance(
            document_id="doc_12",
            filename=doc.filename,
            page_start=table_page.page_number,
            page_end=table_page.page_number,
            block_ids=[table_block.block_id],
            bounding_boxes=[table_block.bbox]
        )
    )

    bundle = resolver.create_evidence_bundle("Pricing schedule", [chunk])
    assert bundle.is_fully_valid is True
    assert len(bundle.evidence_spans) == 1
    span = bundle.evidence_spans[0]
    assert span.is_table is True
    assert span.document_id == "doc_12"
    assert span.page_number == table_page.page_number
    assert span.block_id == table_block.block_id
    assert span.bbox.x1 <= table_page.width + 10.0
