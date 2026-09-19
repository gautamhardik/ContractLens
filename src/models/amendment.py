"""Structured Amendment & Version Intelligence Models for ContractLens (Phase 21).

Provides typed representations for:
- AmendmentResolution: Parent <-> Amendment contract matching with provenance evidence.
- AmendmentChangeType: Taxonomy of modifications (DELETE_AND_REPLACE, ADD_CLAUSE, MODIFY_TERM, CONFIRM_FULL_FORCE, DELETE_CLAUSE).
- SectionAlignment: Aligned parent section and amendment section pairs.
- StructuredAmendmentChange: Detailed change unit capturing before/after text, change type, impact, and dual evidence.
- VersionComparisonReport: Full comparison report containing aligned modifications, preserved provisions, and grounded business impact.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

from src.models.canonical import EvidenceReference, BoundingBox


class AmendmentChangeType(str, Enum):
    """Taxonomy of contractual amendment modifications."""
    DELETE_AND_REPLACE = "DELETE_AND_REPLACE"
    ADD_CLAUSE = "ADD_CLAUSE"
    ADD_COVERAGE = "ADD_COVERAGE"
    MODIFY_TERM = "MODIFY_TERM"
    CONFIRM_FULL_FORCE = "CONFIRM_FULL_FORCE"
    DELETE_CLAUSE = "DELETE_CLAUSE"


class AmendmentResolution(BaseModel):
    """Deterministic resolution connecting an amendment to its base/parent contract."""
    amendment_doc_id: str
    amendment_filename: str
    parent_doc_id: str
    parent_filename: str
    resolution_confidence: float
    resolution_basis: str  # e.g., "explicit_recital_reference", "party_and_title_alignment"
    evidence: EvidenceReference


class StructuredAmendmentChange(BaseModel):
    """Grounded delta for a specific contractual section or clause."""
    change_id: str
    section_number: str
    section_title: str
    change_type: AmendmentChangeType
    before_text: Optional[str] = None
    after_text: str
    amendment_raw_text: str
    impact_summary: str
    parent_evidence: Optional[EvidenceReference] = None
    amendment_evidence: EvidenceReference
    is_superseded: bool = True


class VersionComparisonReport(BaseModel):
    """Consolidated version comparison and amendment intelligence report."""
    parent_doc_id: str
    parent_filename: str
    amendment_doc_id: str
    amendment_filename: str
    resolution: AmendmentResolution
    total_modifications: int
    changes: List[StructuredAmendmentChange] = Field(default_factory=list)
    full_force_confirmed: bool = True
    full_force_evidence: Optional[EvidenceReference] = None
    preserved_provisions_summary: str = "All provisions not expressly modified by the amendment remain in full force and effect."
    business_impact_items: List[str] = Field(default_factory=list)
    comparison_timestamp: str = ""
