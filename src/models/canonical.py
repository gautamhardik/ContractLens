"""Canonical Document Model for ContractLens.

Defines the provenance-first schema representing structured contract documents,
pages, structural blocks, sections, tables, and evidence coordinates.
"""

from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
from pydantic import BaseModel, Field


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    SIGNATURE_BLOCK = "signature_block"
    EXHIBIT_MARKER = "exhibit_marker"
    PAGE_HEADER = "page_header"
    PAGE_FOOTER = "page_footer"
    SEC_NOISE = "sec_noise"
    UNKNOWN = "unknown"


class BoundingBox(BaseModel):
    """Geometric coordinates in PDF points (x0, y0, x1, y1)."""
    x0: float
    y0: float
    x1: float
    y1: float

    def as_tuple(self) -> Tuple[float, float, float, float]:
        return (self.x0, self.y0, self.x1, self.y1)


class EvidenceReference(BaseModel):
    """Immutable provenance pointer for downstream citations and click-to-cite UI."""
    document_id: str
    filename: str
    page_number: int  # 1-indexed
    block_id: str
    bbox: BoundingBox
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    char_offset_start: Optional[int] = None
    char_offset_end: Optional[int] = None


class TableCell(BaseModel):
    """Structured table cell with position and text."""
    row_idx: int
    col_idx: int
    text: str
    is_header: bool = False


class TableRow(BaseModel):
    """Structured table row containing cells."""
    row_idx: int
    cells: List[TableCell] = Field(default_factory=list)


class TableData(BaseModel):
    """Tabular structure extracted from PDF pages."""
    num_rows: int
    num_cols: int
    headers: List[str] = Field(default_factory=list)
    rows: List[TableRow] = Field(default_factory=list)
    raw_matrix: List[List[Optional[str]]] = Field(default_factory=list)


class CanonicalBlock(BaseModel):
    """Fundamental structural block of text or tabular content."""
    block_id: str
    document_id: str
    page_number: int  # 1-indexed
    reading_order: int  # 0-indexed within page
    block_type: BlockType
    bbox: BoundingBox
    raw_text: str
    normalized_text: str
    section_number: Optional[str] = None
    section_title: Optional[str] = None
    parent_section_id: Optional[str] = None
    is_sec_noise: bool = False
    noise_reason: Optional[str] = None
    table_data: Optional[TableData] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_evidence_ref(self, filename: str) -> EvidenceReference:
        return EvidenceReference(
            document_id=self.document_id,
            filename=filename,
            page_number=self.page_number,
            block_id=self.block_id,
            bbox=self.bbox,
            section_number=self.section_number,
            section_title=self.section_title
        )


class CanonicalPage(BaseModel):
    """Single page containing ordered structural blocks and page metadata."""
    page_number: int  # 1-indexed
    width: float
    height: float
    blocks: List[CanonicalBlock] = Field(default_factory=list)
    page_header: Optional[str] = None
    page_footer: Optional[str] = None
    has_tables: bool = False
    has_signatures: bool = False


class CanonicalSection(BaseModel):
    """High-level clause or section grouping one or more blocks."""
    section_id: str
    section_number: str
    section_title: str
    start_page: int
    end_page: int
    block_ids: List[str] = Field(default_factory=list)
    subsections: List["CanonicalSection"] = Field(default_factory=list)


class CanonicalDocument(BaseModel):
    """Canonical representation of an entire parsed contract document."""
    document_id: str
    filename: str
    file_size: int
    page_count: int
    pages: List[CanonicalPage] = Field(default_factory=list)
    sections: List[CanonicalSection] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_all_blocks(self, include_noise: bool = True) -> List[CanonicalBlock]:
        """Flatten and return all blocks in document reading order."""
        blocks = []
        for page in self.pages:
            for b in page.blocks:
                if include_noise or not b.is_sec_noise:
                    blocks.append(b)
        return blocks

    def get_block_by_id(self, block_id: str) -> Optional[CanonicalBlock]:
        for page in self.pages:
            for b in page.blocks:
                if b.block_id == block_id:
                    return b
        return None
