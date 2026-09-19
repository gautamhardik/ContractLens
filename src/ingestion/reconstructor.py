"""Structural Reconstruction Engine for ContractLens.

Converts raw PDF files via PyMuPDF into the Canonical Document Model,
preserving bounding boxes, reading order, headings, tables, signatures,
exhibits, section context, and SEC noise tags.
"""

import os
import re
from typing import List, Optional, Tuple, Dict, Any
import fitz

from src.models.canonical import (
    BlockType,
    BoundingBox,
    TableCell,
    TableRow,
    TableData,
    CanonicalBlock,
    CanonicalPage,
    CanonicalSection,
    CanonicalDocument,
)


class StructuralReconstructor:
    """Deterministic structural parser and canonical document reconstructor."""

    # Heading patterns
    HEADING_PATTERNS = [
        re.compile(r'^(SECTION|ARTICLE|CLAUSE)\s+([0-9A-Z\.]+)\b[:\.\-\s]*(.*)', re.IGNORECASE),
        re.compile(r'^(\d+\.\d+(?:\.\d+)?)\s+([A-Z][A-Za-z0-9\s,\-\(\)\/\']+)$'),
        re.compile(r'^(EXHIBIT|SCHEDULE|APPENDIX|ATTACHMENT)\s+([0-9A-Z\.]+)\b[:\.\-\s]*(.*)', re.IGNORECASE),
        re.compile(r'^(RECITALS|DEFINITIONS|TERM|PAYMENT|TERMINATION|CONFIDENTIALITY|INDEMNIFICATION|LIMITATION OF LIABILITY|NOTICES|MISCELLANEOUS|GENERAL PROVISIONS)\s*$', re.IGNORECASE)
    ]

    # Signature patterns
    SIGNATURE_TRIGGER = re.compile(r'(IN WITNESS WHEREOF|By:\s*|Name:\s*|Title:\s*|Authorized Signature|ACCEPTED AND AGREED)', re.IGNORECASE)

    # Exhibit patterns
    EXHIBIT_TRIGGER = re.compile(r'^(EXHIBIT|SCHEDULE|APPENDIX|ATTACHMENT)\s+([0-9A-Z\.]+)', re.IGNORECASE)

    # List patterns
    LIST_PATTERN = re.compile(r'^(\([a-z0-9]+\)|\d+[\.\)]|[a-z][\.\)]|[•\-\–\—])\s+', re.IGNORECASE)

    # Noise thresholds
    HEADER_ZONE_MAX_Y = 50.0
    FOOTER_ZONE_OFFSET = 50.0

    def __init__(self, header_margin: float = 50.0, footer_margin: float = 50.0):
        self.header_margin = header_margin
        self.footer_margin = footer_margin

    def reconstruct_document(self, filepath: str, document_id: str) -> CanonicalDocument:
        """Parses a PDF file and reconstructs a CanonicalDocument instance."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        doc = fitz.open(filepath)
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        page_count = len(doc)

        canonical_pages: List[CanonicalPage] = []
        canonical_sections: List[CanonicalSection] = []

        current_section_num: Optional[str] = None
        current_section_title: Optional[str] = None
        current_section_block_ids: List[str] = []
        current_section_start_page: int = 1
        current_section_id: Optional[str] = None

        global_block_counter = 0

        for p_idx in range(page_count):
            page = doc[p_idx]
            page_num = p_idx + 1
            page_w = page.rect.width
            page_h = page.rect.height

            # 1. Extract geometric blocks
            raw_blocks = page.get_text("blocks")  # (x0, y0, x1, y1, text, bno, btype)
            # 2. Extract tables on page
            fitz_tables = page.find_tables()
            table_bboxes = [BoundingBox(x0=t.bbox[0], y0=t.bbox[1], x1=t.bbox[2], y1=t.bbox[3]) for t in fitz_tables.tables]

            page_blocks: List[CanonicalBlock] = []
            has_signatures_on_page = False
            has_tables_on_page = len(fitz_tables.tables) > 0

            for b_idx, b in enumerate(raw_blocks):
                x0, y0, x1, y1, text, bno, btype = b
                raw_text = text
                normalized_text = " ".join(text.strip().split())

                if not normalized_text:
                    continue

                global_block_counter += 1
                block_id = f"{document_id}_p{page_num:03d}_b{b_idx+1:02d}"
                bbox = BoundingBox(x0=round(x0, 2), y0=round(y0, 2), x1=round(x1, 2), y1=round(y1, 2))

                # Step A: Identify SEC noise / headers / footers
                is_noise = False
                noise_reason = None

                # Top header zone
                if y0 < self.header_margin:
                    if any(k in normalized_text for k in ["EX-", "Exhibit", "AM", "PM", "sec.gov", "EDGAR"]):
                        is_noise = True
                        noise_reason = "sec_header_zone"

                # Bottom footer zone
                if y1 > (page_h - self.footer_margin):
                    if any(k in normalized_text for k in ["https://", "sec.gov"]) or normalized_text.isdigit() or re.match(r'^\d+\s*\/\s*\d+$', normalized_text):
                        is_noise = True
                        noise_reason = "sec_footer_zone"

                # Step B: Check block type
                classified_type = BlockType.PARAGRAPH

                if is_noise:
                    classified_type = BlockType.SEC_NOISE
                elif self.EXHIBIT_TRIGGER.search(normalized_text) and len(normalized_text) < 120:
                    classified_type = BlockType.EXHIBIT_MARKER
                elif self.SIGNATURE_TRIGGER.search(normalized_text) and (len(normalized_text) < 300 or "Title:" in normalized_text):
                    classified_type = BlockType.SIGNATURE_BLOCK
                    has_signatures_on_page = True
                else:
                    # Check headings
                    heading_match = self._match_heading(normalized_text)
                    if heading_match:
                        classified_type = BlockType.HEADING
                        sec_num, sec_title = heading_match
                        
                        # Close previous section if any
                        if current_section_num and current_section_id:
                            canonical_sections.append(
                                CanonicalSection(
                                    section_id=current_section_id,
                                    section_number=current_section_num,
                                    section_title=current_section_title or "",
                                    start_page=current_section_start_page,
                                    end_page=page_num,
                                    block_ids=list(current_section_block_ids)
                                )
                            )
                            current_section_block_ids = []

                        # Start new section
                        current_section_num = sec_num
                        current_section_title = sec_title
                        current_section_id = f"sec_{sec_num.replace('.', '_').replace(' ', '_')}"
                        current_section_start_page = page_num
                    elif self.LIST_PATTERN.match(normalized_text):
                        classified_type = BlockType.LIST_ITEM

                # Check if block falls inside a table bounding box
                associated_table_data: Optional[TableData] = None
                for t_idx, t_box in enumerate(table_bboxes):
                    if (bbox.y0 >= t_box.y0 - 2) and (bbox.y1 <= t_box.y1 + 2) and (bbox.x0 >= t_box.x0 - 5):
                        # Block is inside or part of a table
                        classified_type = BlockType.TABLE
                        # Extract table data once
                        fitz_t = fitz_tables.tables[t_idx]
                        matrix = fitz_t.extract()
                        rows: List[TableRow] = []
                        for r_i, row in enumerate(matrix):
                            cells = [
                                TableCell(row_idx=r_i, col_idx=c_i, text=cell or "", is_header=(r_i == 0))
                                for c_i, cell in enumerate(row)
                            ]
                            rows.append(TableRow(row_idx=r_i, cells=cells))

                        associated_table_data = TableData(
                            num_rows=len(matrix),
                            num_cols=len(matrix[0]) if matrix else 0,
                            headers=[str(c or "") for c in matrix[0]] if matrix else [],
                            rows=rows,
                            raw_matrix=matrix
                        )
                        break

                current_section_block_ids.append(block_id)

                block_obj = CanonicalBlock(
                    block_id=block_id,
                    document_id=document_id,
                    page_number=page_num,
                    reading_order=b_idx,
                    block_type=classified_type,
                    bbox=bbox,
                    raw_text=raw_text,
                    normalized_text=normalized_text,
                    section_number=current_section_num,
                    section_title=current_section_title,
                    parent_section_id=current_section_id,
                    is_sec_noise=is_noise,
                    noise_reason=noise_reason,
                    table_data=associated_table_data
                )
                page_blocks.append(block_obj)

            canonical_pages.append(
                CanonicalPage(
                    page_number=page_num,
                    width=round(page_w, 2),
                    height=round(page_h, 2),
                    blocks=page_blocks,
                    has_tables=has_tables_on_page,
                    has_signatures=has_signatures_on_page
                )
            )

        # Close final section
        if current_section_num and current_section_id:
            canonical_sections.append(
                CanonicalSection(
                    section_id=current_section_id,
                    section_number=current_section_num,
                    section_title=current_section_title or "",
                    start_page=current_section_start_page,
                    end_page=page_count,
                    block_ids=list(current_section_block_ids)
                )
            )

        doc.close()

        return CanonicalDocument(
            document_id=document_id,
            filename=filename,
            file_size=file_size,
            page_count=page_count,
            pages=canonical_pages,
            sections=canonical_sections,
            metadata={
                "parser": "PyMuPDF",
                "version": fitz.__version__,
                "total_blocks": global_block_counter
            }
        )

    def _match_heading(self, text: str) -> Optional[Tuple[str, str]]:
        """Matches heading patterns returning (section_number, section_title)."""
        clean = text.strip()
        if len(clean) > 150:
            return None  # Headings are concise

        # Pattern 1: SECTION / ARTICLE / CLAUSE X.X Title
        m = self.HEADING_PATTERNS[0].match(clean)
        if m:
            num = f"{m.group(1)} {m.group(2)}"
            title = m.group(3).strip()
            return (num, title)

        # Pattern 2: 1.1 Title
        m = self.HEADING_PATTERNS[1].match(clean)
        if m:
            return (m.group(1), m.group(2).strip())

        # Pattern 3: EXHIBIT / SCHEDULE
        m = self.HEADING_PATTERNS[2].match(clean)
        if m:
            num = f"{m.group(1)} {m.group(2)}"
            title = m.group(3).strip()
            return (num, title)

        # Pattern 4: RECITALS, DEFINITIONS, etc.
        m = self.HEADING_PATTERNS[3].match(clean)
        if m:
            return (m.group(1).upper(), m.group(1).title())

        return None
