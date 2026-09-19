"""Contract Intelligence Schema for ContractLens (Phase 5 & 6).

Defines strongly-typed models for extracted contract facts (parties, dates,
governing laws, payment terms, termination notices, amendment modifications)
with mandatory clause-level provenance and explicit conflict representation.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field

from src.models.canonical import BoundingBox, EvidenceReference


class ExtractionMethod(str, Enum):
    DETERMINISTIC_REGEX = "deterministic_regex"
    DETERMINISTIC_HEURISTIC = "deterministic_heuristic"
    SEMANTIC_INFERENCE = "semantic_inference"
    HYBRID = "hybrid"


class CandidateStatus(str, Enum):
    ACCEPTED = "accepted"
    CONFLICTING = "conflicting"
    UNVERIFIED = "unverified"
    REJECTED = "rejected"


T = TypeVar("T")


class ExtractedField(BaseModel, Generic[T]):
    """Generic wrapper for any extracted contract fact with mandatory provenance."""
    field_name: str
    raw_value: Optional[str] = None
    normalized_value: Optional[T] = None
    confidence: float = 1.0  # 0.0 to 1.0
    extraction_method: ExtractionMethod
    evidence: Optional[EvidenceReference] = None
    is_found: bool = True
    missing_reason: Optional[str] = None

    @classmethod
    def not_found(cls, field_name: str, reason: str = "Clause not found in document") -> "ExtractedField[T]":
        return cls(
            field_name=field_name,
            raw_value=None,
            normalized_value=None,
            confidence=0.0,
            extraction_method=ExtractionMethod.DETERMINISTIC_HEURISTIC,
            evidence=None,
            is_found=False,
            missing_reason=reason
        )


class ConflictedField(BaseModel, Generic[T]):
    """Explicit container for fields where multiple candidate values conflict."""
    field_name: str
    status: CandidateStatus = CandidateStatus.CONFLICTING
    candidates: List[ExtractedField[T]] = Field(default_factory=list)
    resolution_notes: Optional[str] = None


class ContractParty(BaseModel):
    """Identified contracting party."""
    name: str
    role: Optional[str] = None  # e.g., "Client", "Supplier", "Licensor", "Licensee"
    jurisdiction: Optional[str] = None  # e.g., "Delaware", "Texas", "Ontario"
    raw_text: str
    evidence: EvidenceReference


class PaymentTerms(BaseModel):
    """Payment term structure."""
    payment_type: str  # e.g. "Net", "Monthly", "Upon Receipt"
    payment_days: Optional[int] = None  # e.g. 30 for "Net 30"
    raw_text: str
    evidence: EvidenceReference


class TerminationNotice(BaseModel):
    """Termination notice requirements."""
    notice_days: Optional[int] = None  # e.g. 30, 60, 90
    termination_type: str  # e.g. "Convenience", "Breach", "Non-Renewal"
    raw_text: str
    evidence: EvidenceReference


class AmendmentFact(BaseModel):
    """Specific clause modification declared in an amendment."""
    action: str  # e.g. "DELETE_AND_REPLACE", "ADD_COVERAGE", "CONFIRM_FULL_FORCE"
    target_section: str  # e.g. "Section 1.2 Price", "Section 3 Term"
    summary: str
    raw_text: str
    evidence: EvidenceReference


class ContractIntelligence(BaseModel):
    """Consolidated contract intelligence extracted from a CanonicalDocument."""
    document_id: str
    filename: str
    contract_type: ExtractedField[str]
    effective_date: ExtractedField[str]
    expiration_date: ExtractedField[str]
    renewal_language: ExtractedField[str]
    governing_law: ExtractedField[str]
    parties: List[ContractParty] = Field(default_factory=list)
    payment_terms: Optional[ExtractedField[PaymentTerms]] = None
    termination_notice: Optional[ExtractedField[TerminationNotice]] = None
    amendment_facts: List[AmendmentFact] = Field(default_factory=list)
    referenced_schedules: List[str] = Field(default_factory=list)
    conflicts: Dict[str, ConflictedField[Any]] = Field(default_factory=dict)
    extraction_timestamp: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
