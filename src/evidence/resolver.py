"""Deterministic Evidence Resolver and Bundler for ContractLens (Phase 15).

Implements EvidenceResolver:
1. Resolves retrieved chunks against an in-memory CanonicalDocument repository.
2. Resolves exact canonical blocks, raw source text, and bounding boxes.
3. Detects and reports provenance inconsistencies (e.g. block/page mismatch, invalid bboxes).
4. Deduplicates overlapping canonical blocks while preserving retrieval provenance pointers.
5. Produces validated EvidenceCitation objects.
6. Packages output into a deterministic, reproducible EvidenceBundle sorted by canonical reading order.
"""

import time
from typing import List, Dict, Optional, Tuple, Set, Union
from collections import defaultdict

from src.models.canonical import CanonicalDocument, CanonicalPage, CanonicalBlock, BoundingBox
from src.models.chunk import RetrievalChunk
from src.evidence.models import (
    ValidationStatus,
    EvidenceSpan,
    EvidenceCitation,
    EvidenceValidation,
    EvidenceBundle,
)
from src.evidence.validator import EvidenceValidator


class EvidenceResolver:
    """Deterministic resolver mapping retrieval chunks to verified canonical evidence."""

    def __init__(self, documents: Optional[List[CanonicalDocument]] = None):
        self.doc_map: Dict[str, CanonicalDocument] = {}
        # Pre-index blocks for O(1) resolution: (doc_id, block_id) -> (CanonicalBlock, page_number)
        self.block_index: Dict[Tuple[str, str], Tuple[CanonicalBlock, int]] = {}

        if documents:
            for d in documents:
                self.register_document(d)

    def register_document(self, doc: CanonicalDocument) -> None:
        """Register a CanonicalDocument into the in-memory resolver index."""
        self.doc_map[doc.document_id] = doc
        for page in doc.pages:
            for block in page.blocks:
                self.block_index[(doc.document_id, block.block_id)] = (block, page.page_number)

    def resolve_chunk(self, chunk: RetrievalChunk) -> Tuple[List[EvidenceSpan], List[EvidenceCitation], List[EvidenceValidation]]:
        """Resolve a single RetrievalChunk into verified EvidenceSpans and EvidenceCitations.

        Never invents missing provenance. If an ID or block is invalid, explicit
        validation failures are recorded.
        """
        spans: List[EvidenceSpan] = []
        citations: List[EvidenceCitation] = []
        validations: List[EvidenceValidation] = []

        doc_id = chunk.document_id
        doc = self.doc_map.get(doc_id)
        prov = chunk.provenance

        if not prov.block_ids:
            val = EvidenceValidation(
                status=ValidationStatus.MISSING_PROVENANCE,
                is_valid=False,
                document_resolved=doc is not None,
                page_resolved=False,
                block_resolved=False,
                text_resolved=False,
                bbox_valid=False,
                provenance_consistent=False,
                failure_reasons=["Chunk provenance contains no block_ids."],
            )
            validations.append(val)
            return spans, citations, validations

        for idx, block_id in enumerate(prov.block_ids):
            # Check bbox if available for this block index
            bbox_candidate = prov.bounding_boxes[idx] if idx < len(prov.bounding_boxes) else None

            # Attempt to determine target page from block index or fall back to chunk page range
            indexed = self.block_index.get((doc_id, block_id))
            target_page_num = indexed[1] if indexed else prov.page_start

            val = EvidenceValidator.validate_block_reference(
                doc=doc,
                document_id=doc_id,
                page_number=target_page_num,
                block_id=block_id,
                bbox=bbox_candidate,
            )
            validations.append(val)

            citation = EvidenceCitation(
                document_id=doc_id,
                filename=prov.filename,
                page_number=target_page_num,
                block_id=block_id,
                bbox=bbox_candidate if bbox_candidate else (indexed[0].bbox if indexed else BoundingBox(x0=0.0, y0=0.0, x1=0.0, y1=0.0)),
                section_number=prov.section_number,
                section_title=prov.section_title,
                is_valid=val.is_valid,
                validation_status=val.status,
                validation_reason="; ".join(val.failure_reasons) if val.failure_reasons else None,
                source_chunk_id=chunk.chunk_id,
            )
            citations.append(citation)

            if val.is_valid and indexed:
                block, page_num = indexed
                span = EvidenceSpan(
                    document_id=doc_id,
                    filename=prov.filename,
                    page_number=page_num,
                    block_id=block.block_id,
                    reading_order=block.reading_order,
                    raw_text=block.raw_text,
                    normalized_text=block.normalized_text,
                    bbox=block.bbox,
                    section_number=block.section_number or prov.section_number,
                    section_title=block.section_title or prov.section_title,
                    block_type=block.block_type.value,
                    is_table=block.table_data is not None,
                    metadata={"source_chunk_id": chunk.chunk_id, "reading_order": block.reading_order},
                )
                spans.append(span)

        return spans, citations, validations

    def create_evidence_bundle(
        self,
        query: str,
        retrieved_chunks: List[RetrievalChunk],
    ) -> EvidenceBundle:
        """Resolve a set of retrieved chunks and assemble an immutable EvidenceBundle.

        Performs deterministic deduplication: identical canonical blocks referenced by
        multiple chunks are merged into a single EvidenceSpan with aggregated chunk linkage.
        Sorts evidence spans strictly by: document_id, page_number, reading_order, block_id.
        """
        start_time = time.perf_counter()

        all_spans_by_key: Dict[Tuple[str, int, str], EvidenceSpan] = {}
        span_chunk_sources: Dict[Tuple[str, int, str], List[str]] = defaultdict(list)
        all_citations: List[EvidenceCitation] = []
        all_validations: List[EvidenceValidation] = []

        for chunk in retrieved_chunks:
            spans, citations, validations = self.resolve_chunk(chunk)
            all_citations.extend(citations)
            all_validations.extend(validations)

            for span in spans:
                key = (span.document_id, span.page_number, span.block_id)
                if key not in all_spans_by_key:
                    all_spans_by_key[key] = span
                span_chunk_sources[key].append(chunk.chunk_id)

        # Attach aggregated source chunks to span metadata
        for key, span in all_spans_by_key.items():
            span.metadata["source_chunk_ids"] = sorted(list(set(span_chunk_sources[key])))

        # Deterministic sorting: (document_id, page_number, reading_order, block_id)
        sorted_spans = sorted(
            all_spans_by_key.values(),
            key=lambda s: (s.document_id, s.page_number, s.reading_order, s.block_id)
        )

        valid_citations = sum(1 for c in all_citations if c.is_valid)
        is_fully_valid = len(all_validations) > 0 and all(v.is_valid for v in all_validations)

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return EvidenceBundle(
            query=query,
            retrieved_chunks=retrieved_chunks,
            evidence_spans=sorted_spans,
            citations=all_citations,
            validation_reports=all_validations,
            is_fully_valid=is_fully_valid,
            total_spans=len(sorted_spans),
            valid_citations_count=valid_citations,
            resolution_latency_ms=latency_ms,
            metadata={
                "total_chunks_evaluated": len(retrieved_chunks),
                "total_raw_citations": len(all_citations),
                "unique_spans_count": len(sorted_spans),
            }
        )
