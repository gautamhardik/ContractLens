"""Grounded RAG Data Models for ContractLens (Phase 16).

Defines typed representations for:
- ClaimVerificationStatus: Formal verification outcomes (SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, INSUFFICIENT_EVIDENCE).
- GroundedClaim: An extracted factual assertion with explicit evidence linkage.
- VerificationResult: Detailed independent evaluation report for a single claim.
- GroundedAnswer: The synthesized answer bound to verified citations and claims.
- RAGResponse: Complete end-to-end payload containing the answer, claims, bundle, and metrics.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.evidence.models import EvidenceSpan, EvidenceCitation, EvidenceBundle


class ClaimVerificationStatus(str, Enum):
    """Formal verification status of a contractual claim against evidence."""
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class GroundedClaim(BaseModel):
    """A factual claim asserted by the LLM, proposing linkage to evidence IDs."""
    claim_id: str
    text: str
    evidence_ids: List[str] = Field(default_factory=list)
    is_verified: bool = False
    verification_status: ClaimVerificationStatus = ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
    confidence: float = 1.0
    verification_reason: Optional[str] = None


class VerificationResult(BaseModel):
    """Independent audit result assessing whether evidence actually supports a claim."""
    claim_id: str
    status: ClaimVerificationStatus
    evidence_ids: List[str]
    is_supported: bool
    reason: str
    resolved_citations: List[EvidenceCitation] = Field(default_factory=list)
    confidence: float = 1.0


class VerificationReport(BaseModel):
    """Summary report across all claims in a generated answer."""
    total_claims: int = 0
    supported_claims: int = 0
    partially_supported_claims: int = 0
    unsupported_claims: int = 0
    contradicted_claims: int = 0
    insufficient_evidence_claims: int = 0
    claim_support_rate: float = 0.0
    unsupported_claim_rate: float = 0.0
    contradiction_rate: float = 0.0
    citation_precision: float = 1.0
    citation_recall: float = 1.0
    is_fully_grounded: bool = False
    results: List[VerificationResult] = Field(default_factory=list)


class GroundedAnswer(BaseModel):
    """Synthesized business-readable contractual answer with verified citations."""
    query: str
    answer_text: str
    claims: List[GroundedClaim] = Field(default_factory=list)
    citations: List[EvidenceCitation] = Field(default_factory=list)
    verification_report: VerificationReport
    is_insufficient_evidence: bool = False
    grounding_status: ClaimVerificationStatus = ClaimVerificationStatus.SUPPORTED


class RAGResponse(BaseModel):
    """Full top-level response container for Phase 16 execution."""
    query: str
    answer: GroundedAnswer
    evidence_bundle: EvidenceBundle
    retrieval_latency_ms: float = 0.0
    evidence_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    verification_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
