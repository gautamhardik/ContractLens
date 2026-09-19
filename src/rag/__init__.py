"""Grounded RAG and Claim Verification Package for ContractLens (Phase 16).

Exports:
- Models: ClaimVerificationStatus, GroundedClaim, VerificationResult, VerificationReport, GroundedAnswer, RAGResponse
- Generator & Providers: BaseLLMProvider, FakeLLMProvider, GeminiLLMProvider, GroundedAnswerGenerator
- Verifier: ClaimVerifier
- Pipeline: GroundedRAGPipeline
"""

from src.rag.models import (
    ClaimVerificationStatus,
    GroundedClaim,
    VerificationResult,
    VerificationReport,
    GroundedAnswer,
    RAGResponse,
)
from src.rag.generator import (
    BaseLLMProvider,
    FakeLLMProvider,
    GeminiLLMProvider,
    GroundedAnswerGenerator,
)
from src.rag.verifier import ClaimVerifier
from src.rag.pipeline import GroundedRAGPipeline

__all__ = [
    "ClaimVerificationStatus",
    "GroundedClaim",
    "VerificationResult",
    "VerificationReport",
    "GroundedAnswer",
    "RAGResponse",
    "BaseLLMProvider",
    "FakeLLMProvider",
    "GeminiLLMProvider",
    "GroundedAnswerGenerator",
    "ClaimVerifier",
    "GroundedRAGPipeline",
]
