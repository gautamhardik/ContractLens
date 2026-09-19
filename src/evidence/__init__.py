"""ContractLens Evidence Layer Package (Phase 15).

Exports the deterministic evidence resolution and citation integrity components:
- Models: ValidationStatus, EvidenceSpan, EvidenceCitation, EvidenceValidation, EvidenceBundle
- Validator: EvidenceValidator
- Resolver: EvidenceResolver
"""

from src.evidence.models import (
    ValidationStatus,
    EvidenceSpan,
    EvidenceCitation,
    EvidenceValidation,
    EvidenceBundle,
)
from src.evidence.validator import EvidenceValidator
from src.evidence.resolver import EvidenceResolver

__all__ = [
    "ValidationStatus",
    "EvidenceSpan",
    "EvidenceCitation",
    "EvidenceValidation",
    "EvidenceBundle",
    "EvidenceValidator",
    "EvidenceResolver",
]
