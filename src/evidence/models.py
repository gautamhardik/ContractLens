"""Evidence Layer Models for ContractLens (Phase 15).

Defines strongly-typed, immutable evidence representations:
- ValidationStatus: Deterministic status enumeration.
- EvidenceSpan: Granular supporting text span anchored to a canonical block and bounding box.
- EvidenceCitation: Verifiable citation pointing to authoritative document coordinates.
- EvidenceValidation: Granular validation checks for provenance integrity.
- EvidenceBundle: Standardized container delivered to downstream Grounded RAG (Phase 16).
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

from src.models.canonical import BoundingBox
from src.models.chunk import RetrievalChunk


class ValidationStatus(str, Enum):
    """Deterministic validation status for evidence resolution and citation verification."""
    VALID = "valid"
    INVALID_DOCUMENT = "invalid_document"
    INVALID_PAGE = "invalid_page"
    INVALID_BLOCK = "invalid_block"
    MISSING_TEXT = "missing_text"
    INVALID_BBOX = "invalid_bbox"
    INCONSISTENT_PROVENANCE = "inconsistent_provenance"
    MISSING_PROVENANCE = "missing_provenance"


class EvidenceSpan(BaseModel):
    """Precise supporting canonical text span with exact bounding-box coordinates."""
    document_id: str
    filename: str
    page_number: int  # 1-indexed
    block_id: str
    reading_order: int
    raw_text: str
    normalized_text: Optional[str] = None
    bbox: BoundingBox
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    block_type: str = "paragraph"
    is_table: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_citation_string(self) -> str:
        """Human-readable citation identifier, e.g. 'doc_03 (Page 12, §18.4)'."""
        sec = f", §{self.section_number}" if self.section_number else ""
        return f"{self.document_id} (Page {self.page_number}{sec})"


class EvidenceCitation(BaseModel):
    """Authoritative citation pointer that downstream RAG can safely quote and link."""
    document_id: str
    filename: str
    page_number: int
    block_id: str
    bbox: BoundingBox
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    is_valid: bool = False
    validation_status: ValidationStatus = ValidationStatus.VALID
    validation_reason: Optional[str] = None
    source_chunk_id: Optional[str] = None


class EvidenceValidation(BaseModel):
    """Comprehensive provenance and structural check report for an evidence span or chunk."""
    status: ValidationStatus
    is_valid: bool
    document_resolved: bool
    page_resolved: bool
    block_resolved: bool
    text_resolved: bool
    bbox_valid: bool
    provenance_consistent: bool
    failure_reasons: List[str] = Field(default_factory=list)


class EvidenceBundle(BaseModel):
    """Formal interface connecting Retrieval to Grounded RAG (Phase 16).

    Preserves full retrieval provenance, deduplicated evidence spans in canonical
    reading order, validated citations, and comprehensive validation summaries.
    """
    query: str
    retrieved_chunks: List[RetrievalChunk] = Field(default_factory=list)
    evidence_spans: List[EvidenceSpan] = Field(default_factory=list)
    citations: List[EvidenceCitation] = Field(default_factory=list)
    validation_reports: List[EvidenceValidation] = Field(default_factory=list)
    is_fully_valid: bool = False
    total_spans: int = 0
    valid_citations_count: int = 0
    resolution_latency_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
