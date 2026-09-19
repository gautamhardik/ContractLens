"""Targeted tests for Canonical Document Model and Structural Reconstruction.
"""

import os
import json
import pytest
from src.models.canonical import (
    BlockType,
    BoundingBox,
    EvidenceReference,
    CanonicalDocument,
    CanonicalPage,
    CanonicalBlock
)
from src.ingestion.reconstructor import StructuralReconstructor


import re

RAW_DIR = r"c:\Users\hiten\Downloads\ContractLens\Data\raw"


def get_raw_path(needle: str) -> str:
    """Find file in Data/raw by alphanumeric substring match."""
    needle_clean = re.sub(r'[^a-zA-Z0-9]', '', needle).lower()
    for f in os.listdir(RAW_DIR):
        f_clean = re.sub(r'[^a-zA-Z0-9]', '', f).lower()
        if needle_clean in f_clean:
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(f"File matching '{needle}' not found in {RAW_DIR}")


class TestCanonicalModel:
    def test_bounding_box_tuple(self):
        bbox = BoundingBox(x0=10.0, y0=20.0, x1=100.0, y1=200.0)
        assert bbox.as_tuple() == (10.0, 20.0, 100.0, 200.0)

    def test_canonical_block_to_evidence_ref(self):
        block = CanonicalBlock(
            block_id="doc_01_p001_b01",
            document_id="doc_01",
            page_number=1,
            reading_order=0,
            block_type=BlockType.PARAGRAPH,
            bbox=BoundingBox(x0=10.0, y0=20.0, x1=100.0, y1=50.0),
            raw_text="Sample clause text",
            normalized_text="Sample clause text",
            section_number="1.1",
            section_title="Definitions"
        )
        ref = block.to_evidence_ref("sample_contract.pdf")
        assert isinstance(ref, EvidenceReference)
        assert ref.document_id == "doc_01"
        assert ref.page_number == 1
        assert ref.section_number == "1.1"
        assert ref.section_title == "Definitions"
        assert ref.bbox.x0 == 10.0

    def test_document_serialization(self):
        doc = CanonicalDocument(
            document_id="test_doc",
            filename="test.pdf",
            file_size=1024,
            page_count=1,
            pages=[
                CanonicalPage(
                    page_number=1,
                    width=612.0,
                    height=792.0,
                    blocks=[
                        CanonicalBlock(
                            block_id="test_doc_p001_b01",
                            document_id="test_doc",
                            page_number=1,
                            reading_order=0,
                            block_type=BlockType.HEADING,
                            bbox=BoundingBox(x0=50.0, y0=60.0, x1=500.0, y1=80.0),
                            raw_text="1. Term",
                            normalized_text="1. Term",
                            section_number="1",
                            section_title="Term"
                        )
                    ]
                )
            ]
        )
        json_data = doc.model_dump_json()
        restored = CanonicalDocument.model_validate_json(json_data)
        assert restored.document_id == "test_doc"
        assert len(restored.pages) == 1
        assert restored.pages[0].blocks[0].section_number == "1"


class TestStructuralReconstructor:
    @pytest.fixture
    def reconstructor(self):
        return StructuralReconstructor()

    def test_access_etrade_amendment(self, reconstructor):
        """Test on short 3-page version comparison ground truth."""
        path = get_raw_path("Access-E-TRADE Amendment")
        doc = reconstructor.reconstruct_document(path, "doc_02")

        assert doc.document_id == "doc_02"
        assert doc.page_count == 3
        assert len(doc.pages) == 3

        all_blocks = doc.get_all_blocks(include_noise=True)
        assert len(all_blocks) > 0

        # Verify SEC noise was tagged
        noise_blocks = [b for b in all_blocks if b.is_sec_noise]
        assert len(noise_blocks) > 0
        for nb in noise_blocks:
            assert nb.noise_reason in ("sec_header_zone", "sec_footer_zone")
            assert nb.block_type == BlockType.SEC_NOISE

        # Verify clean blocks preserve section context
        clean_blocks = doc.get_all_blocks(include_noise=False)
        assert len(clean_blocks) > 0
        # Ensure bounding boxes are present on every block
        for b in clean_blocks:
            assert b.bbox.x0 is not None
            assert b.bbox.y0 is not None
            assert b.raw_text != ""

    def test_square_marqeta_tables(self, reconstructor):
        """Test on Square-Marqeta (contains fee tables)."""
        path = get_raw_path("Square-Marqeta")
        doc = reconstructor.reconstruct_document(path, "doc_16")

        assert doc.page_count == 63
        table_blocks = [b for b in doc.get_all_blocks() if b.block_type == BlockType.TABLE]
        assert len(table_blocks) > 0
        # Verify table_data was attached
        assert table_blocks[0].table_data is not None
        assert table_blocks[0].table_data.num_rows > 0

    def test_sabredxc_stress(self, reconstructor):
        """Test on 176-page large document."""
        path = get_raw_path("Sabre-DXC")
        doc = reconstructor.reconstruct_document(path, "doc_10")

        assert doc.page_count == 176
        assert len(doc.pages) == 176
        assert len(doc.sections) > 0
