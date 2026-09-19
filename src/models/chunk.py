"""Chunk Schema for ContractLens (Phase 11 & 12).

Defines strongly-typed retrieval chunk representations that maintain immutable
provenance pointers back to CanonicalDocument blocks, coordinates, pages, and sections.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

from src.models.canonical import BoundingBox, EvidenceReference


class ChunkType(str, Enum):
    SECTION = "section"
    SUBSECTION = "subsection"
    PARAGRAPH_GROUP = "paragraph_group"
    TABLE = "table"
    SLIDING_WINDOW = "sliding_window"
    EXHIBIT = "exhibit"


class ChunkProvenance(BaseModel):
    """Immutable provenance tracking connecting a chunk to underlying canonical blocks."""
    document_id: str
    filename: str
    page_start: int
    page_end: int
    block_ids: List[str]
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    bounding_boxes: List[BoundingBox] = Field(default_factory=list)

    def to_evidence_ref(self) -> EvidenceReference:
        """Create a primary EvidenceReference from the chunk's first block."""
        first_bbox = self.bounding_boxes[0] if self.bounding_boxes else BoundingBox(x0=0.0, y0=0.0, x1=0.0, y1=0.0)
        return EvidenceReference(
            document_id=self.document_id,
            filename=self.filename,
            page_number=self.page_start,
            block_id=self.block_ids[0] if self.block_ids else "chunk_root",
            bbox=first_bbox,
            section_number=self.section_number,
            section_title=self.section_title
        )


class RetrievalChunk(BaseModel):
    """Standardized retrieval unit produced by any interchangeable chunker."""
    chunk_id: str
    document_id: str
    chunk_type: ChunkType
    text: str
    char_count: int
    token_estimate: int
    provenance: ChunkProvenance
    metadata: Dict[str, Any] = Field(default_factory=dict)
