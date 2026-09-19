"""Citation and Provenance Validator for ContractLens (Phase 15).

Deterministic validator verifying:
1. Document existence and identity match.
2. Page bounds and existence in CanonicalDocument.
3. Block existence, text presence, and page ownership.
4. Bounding box geometric validity (x0 <= x1, y0 <= y1, within page dimensions).
5. Internal consistency of provenance chain.
"""

from typing import Optional, List, Tuple
from src.models.canonical import CanonicalDocument, CanonicalPage, CanonicalBlock, BoundingBox
from src.evidence.models import ValidationStatus, EvidenceValidation, EvidenceCitation, EvidenceSpan


class EvidenceValidator:
    """Deterministic structural and geometric provenance validator."""

    @staticmethod
    def validate_bounding_box(bbox: BoundingBox, page_width: Optional[float] = None, page_height: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """Validate geometric structure and page dimension boundaries."""
        if bbox.x0 > bbox.x1:
            return False, f"Invalid bbox: x0 ({bbox.x0}) > x1 ({bbox.x1})"
        if bbox.y0 > bbox.y1:
            return False, f"Invalid bbox: y0 ({bbox.y0}) > y1 ({bbox.y1})"
        if bbox.x0 < 0 or bbox.y0 < 0:
            return False, f"Invalid bbox: negative coordinates ({bbox.x0}, {bbox.y0})"

        if page_width is not None and bbox.x1 > page_width + 10.0:  # slight buffer for bleed
            return False, f"Invalid bbox: x1 ({bbox.x1}) exceeds page width ({page_width})"
        if page_height is not None and bbox.y1 > page_height + 10.0:
            return False, f"Invalid bbox: y1 ({bbox.y1}) exceeds page height ({page_height})"

        return True, None

    @classmethod
    def validate_block_reference(
        cls,
        doc: Optional[CanonicalDocument],
        document_id: str,
        page_number: int,
        block_id: str,
        bbox: Optional[BoundingBox] = None,
    ) -> EvidenceValidation:
        """Validate a block citation reference against a canonical document."""
        failures: List[str] = []
        doc_resolved = False
        page_resolved = False
        block_resolved = False
        text_resolved = False
        bbox_valid = False
        provenance_consistent = False

        # 1. Document Resolution
        if doc is None:
            failures.append(f"Document '{document_id}' could not be resolved in corpus.")
            return EvidenceValidation(
                status=ValidationStatus.INVALID_DOCUMENT,
                is_valid=False,
                document_resolved=False,
                page_resolved=False,
                block_resolved=False,
                text_resolved=False,
                bbox_valid=False,
                provenance_consistent=False,
                failure_reasons=failures,
            )
        doc_resolved = True

        if doc.document_id != document_id:
            failures.append(f"Document ID mismatch: expected '{document_id}', got '{doc.document_id}'.")

        # 2. Page Resolution
        target_page: Optional[CanonicalPage] = None
        for p in doc.pages:
            if p.page_number == page_number:
                target_page = p
                break

        if target_page is None:
            failures.append(f"Page {page_number} not found in document '{document_id}' (total pages: {doc.page_count}).")
            status = ValidationStatus.INVALID_PAGE
        else:
            page_resolved = True

        # 3. Block Resolution
        target_block: Optional[CanonicalBlock] = None
        found_in_another_page = None
        for p in doc.pages:
            for b in p.blocks:
                if b.block_id == block_id:
                    if p.page_number == page_number:
                        target_block = b
                    else:
                        found_in_another_page = p.page_number
                    break
            if target_block:
                break

        if target_block is None:
            if found_in_another_page is not None:
                failures.append(f"Block '{block_id}' claimed on page {page_number}, but belongs to page {found_in_another_page}.")
                status = ValidationStatus.INCONSISTENT_PROVENANCE
            else:
                failures.append(f"Block '{block_id}' not found in document '{document_id}'.")
                status = ValidationStatus.INVALID_BLOCK
        else:
            block_resolved = True

            # 4. Text Resolution
            raw_text = target_block.raw_text.strip()
            if not raw_text:
                failures.append(f"Block '{block_id}' has empty source text.")
                status = ValidationStatus.MISSING_TEXT
            else:
                text_resolved = True

            # 5. Bounding Box Validation
            box_to_check = bbox if bbox is not None else target_block.bbox
            p_width = target_page.width if target_page else None
            p_height = target_page.height if target_page else None
            is_box_ok, box_err = cls.validate_bounding_box(box_to_check, p_width, p_height)
            if not is_box_ok:
                failures.append(box_err or "Invalid bounding box coordinates.")
                status = ValidationStatus.INVALID_BBOX
            else:
                bbox_valid = True

        # 6. Overall Consistency
        if doc_resolved and page_resolved and block_resolved and text_resolved and bbox_valid:
            provenance_consistent = True
            status = ValidationStatus.VALID

        is_valid = len(failures) == 0 and provenance_consistent

        return EvidenceValidation(
            status=status,
            is_valid=is_valid,
            document_resolved=doc_resolved,
            page_resolved=page_resolved,
            block_resolved=block_resolved,
            text_resolved=text_resolved,
            bbox_valid=bbox_valid,
            provenance_consistent=provenance_consistent,
            failure_reasons=failures,
        )
