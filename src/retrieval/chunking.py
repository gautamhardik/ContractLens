"""Chunking Strategies for ContractLens (Phase 11).

Implements interchangeable chunking strategies:
A. FixedSlidingWindowChunker: Baseline token/character window with overlap.
B. SectionAwareChunker: Structural chunking respecting contract section headers,
   subsections, lists, tables, and exhibit boundaries with full provenance retention.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from src.models.canonical import CanonicalDocument, CanonicalBlock, BlockType, BoundingBox
from src.models.chunk import RetrievalChunk, ChunkProvenance, ChunkType


class BaseChunker(ABC):
    """Abstract interface for all ContractLens chunking strategies."""

    @abstractmethod
    def chunk(self, doc: CanonicalDocument) -> List[RetrievalChunk]:
        """Convert a CanonicalDocument into structured RetrievalChunks."""
        pass


class FixedSlidingWindowChunker(BaseChunker):
    """Baseline fixed-size window chunker with overlapping boundaries."""

    def __init__(self, target_chars: int = 1000, overlap_chars: int = 200):
        self.target_chars = target_chars
        self.overlap_chars = overlap_chars

    def chunk(self, doc: CanonicalDocument) -> List[RetrievalChunk]:
        chunks: List[RetrievalChunk] = []
        blocks = doc.get_all_blocks(include_noise=False)

        if not blocks:
            return chunks

        current_blocks: List[CanonicalBlock] = []
        current_text = ""
        chunk_idx = 1

        for block in blocks:
            text = block.raw_text.strip()
            if not text:
                continue

            current_blocks.append(block)
            current_text += ("\n\n" if current_text else "") + text

            if len(current_text) >= self.target_chars:
                chunk = self._create_chunk(doc, chunk_idx, current_blocks, current_text)
                chunks.append(chunk)
                chunk_idx += 1

                # Retain overlap blocks if possible
                overlap_text = ""
                retained_blocks: List[CanonicalBlock] = []
                for b in reversed(current_blocks):
                    overlap_text = b.raw_text + ("\n\n" if overlap_text else "") + overlap_text
                    retained_blocks.insert(0, b)
                    if len(overlap_text) >= self.overlap_chars:
                        break

                current_blocks = retained_blocks
                current_text = overlap_text

        # Remaining tail
        if current_blocks and len(current_text.strip()) > 30:
            chunk = self._create_chunk(doc, chunk_idx, current_blocks, current_text)
            chunks.append(chunk)

        return chunks

    def _create_chunk(
        self,
        doc: CanonicalDocument,
        idx: int,
        blocks: List[CanonicalBlock],
        text: str
    ) -> RetrievalChunk:
        page_start = min(b.page_number for b in blocks)
        page_end = max(b.page_number for b in blocks)
        block_ids = [b.block_id for b in blocks]
        bboxes = [b.bbox for b in blocks]

        prov = ChunkProvenance(
            document_id=doc.document_id,
            filename=doc.filename,
            page_start=page_start,
            page_end=page_end,
            block_ids=block_ids,
            section_number=blocks[0].section_number,
            section_title=blocks[0].section_title,
            bounding_boxes=bboxes
        )

        return RetrievalChunk(
            chunk_id=f"chk_win_{doc.document_id}_{idx:03d}",
            document_id=doc.document_id,
            chunk_type=ChunkType.SLIDING_WINDOW,
            text=text.strip(),
            char_count=len(text.strip()),
            token_estimate=len(text.strip()) // 4,
            provenance=prov,
            metadata={"strategy": "fixed_sliding_window", "block_count": len(blocks)}
        )


class SectionAwareChunker(BaseChunker):
    """Structural chunking strategy preserving contract section hierarchy and tables."""

    def __init__(self, max_chars: int = 2500, min_chars: int = 150):
        self.max_chars = max_chars
        self.min_chars = min_chars

    def chunk(self, doc: CanonicalDocument) -> List[RetrievalChunk]:
        chunks: List[RetrievalChunk] = []
        blocks = doc.get_all_blocks(include_noise=False)

        if not blocks:
            return chunks

        # Group blocks by section or logical units
        current_section_key = None
        current_blocks: List[CanonicalBlock] = []
        chunk_idx = 1

        for block in blocks:
            # Standalone table chunks if substantial
            if block.block_type == BlockType.TABLE and block.table_data:
                # Flush existing buffer
                if current_blocks:
                    c = self._build_section_chunk(doc, chunk_idx, current_blocks)
                    chunks.append(c)
                    chunk_idx += 1
                    current_blocks = []
                    current_section_key = None

                # Table chunk
                prov = ChunkProvenance(
                    document_id=doc.document_id,
                    filename=doc.filename,
                    page_start=block.page_number,
                    page_end=block.page_number,
                    block_ids=[block.block_id],
                    section_number=block.section_number,
                    section_title=block.section_title or "Table",
                    bounding_boxes=[block.bbox]
                )
                tbl_text = block.raw_text.strip()
                chunks.append(RetrievalChunk(
                    chunk_id=f"chk_tbl_{doc.document_id}_{chunk_idx:03d}",
                    document_id=doc.document_id,
                    chunk_type=ChunkType.TABLE,
                    text=tbl_text,
                    char_count=len(tbl_text),
                    token_estimate=len(tbl_text) // 4,
                    provenance=prov,
                    metadata={"strategy": "section_aware_table", "rows": block.table_data.num_rows}
                ))
                chunk_idx += 1
                continue

            sec_key = (block.section_number, block.section_title)

            # Check if entering a new major section
            is_new_section = (
                block.block_type in (BlockType.HEADING, BlockType.EXHIBIT_MARKER) or
                (sec_key != current_section_key and sec_key[0] is not None)
            )

            current_len = sum(len(b.raw_text) for b in current_blocks)

            if is_new_section and current_blocks and current_len >= self.min_chars:
                # Flush previous section
                c = self._build_section_chunk(doc, chunk_idx, current_blocks)
                chunks.append(c)
                chunk_idx += 1
                current_blocks = [block]
                current_section_key = sec_key
            elif current_len + len(block.raw_text) > self.max_chars and current_blocks:
                # Section is very large (e.g. 5 pages long); split cleanly on paragraph boundary
                c = self._build_section_chunk(doc, chunk_idx, current_blocks)
                chunks.append(c)
                chunk_idx += 1
                current_blocks = [block]
                current_section_key = sec_key
            else:
                current_blocks.append(block)
                if sec_key[0] or sec_key[1]:
                    current_section_key = sec_key

        if current_blocks:
            c = self._build_section_chunk(doc, chunk_idx, current_blocks)
            chunks.append(c)

        return chunks

    def _build_section_chunk(
        self,
        doc: CanonicalDocument,
        idx: int,
        blocks: List[CanonicalBlock]
    ) -> RetrievalChunk:
        page_start = min(b.page_number for b in blocks)
        page_end = max(b.page_number for b in blocks)
        block_ids = [b.block_id for b in blocks]
        bboxes = [b.bbox for b in blocks]

        # Section meta
        sec_num = next((b.section_number for b in blocks if b.section_number), None)
        sec_title = next((b.section_title for b in blocks if b.section_title), None)

        is_exhibit = any(b.block_type == BlockType.EXHIBIT_MARKER for b in blocks)
        chunk_type = ChunkType.EXHIBIT if is_exhibit else (
            ChunkType.SECTION if sec_num else ChunkType.PARAGRAPH_GROUP
        )

        text = "\n\n".join(b.raw_text.strip() for b in blocks if b.raw_text.strip())

        prov = ChunkProvenance(
            document_id=doc.document_id,
            filename=doc.filename,
            page_start=page_start,
            page_end=page_end,
            block_ids=block_ids,
            section_number=sec_num,
            section_title=sec_title,
            bounding_boxes=bboxes
        )

        return RetrievalChunk(
            chunk_id=f"chk_sec_{doc.document_id}_{idx:03d}",
            document_id=doc.document_id,
            chunk_type=chunk_type,
            text=text,
            char_count=len(text),
            token_estimate=len(text) // 4,
            provenance=prov,
            metadata={
                "strategy": "section_aware",
                "block_count": len(blocks),
                "is_cross_page": page_start != page_end
            }
        )
