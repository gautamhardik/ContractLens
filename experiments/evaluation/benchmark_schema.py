"""Golden Evaluation Dataset Models for ContractLens (Phase 10).

Defines strongly-typed representations for evaluation benchmark items, evidence requirements,
reasoning categories, and multi-answer/unanswerable gold standards.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionCategory(str, Enum):
    METADATA = "metadata"
    PARTIES = "parties"
    DATES_LIFECYCLE = "dates_lifecycle"
    PAYMENT = "payment"
    TERMINATION = "termination"
    OBLIGATIONS = "obligations"
    CROSS_DOCUMENT = "cross_document"
    AMENDMENTS_VERSIONS = "amendments_versions"


class ReasoningType(str, Enum):
    DIRECT_LOOKUP = "direct_lookup"
    PARAPHRASED_LOOKUP = "paraphrased_lookup"
    MULTI_HOP = "multi_hop"
    TEMPORAL_REASONING = "temporal_reasoning"
    AMENDMENT_PRECEDENCE = "amendment_precedence"
    CROSS_CONTRACT = "cross_contract"
    UNANSWERABLE = "unanswerable"
    TABLE_LOOKUP = "table_lookup"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ExpectedEvidence(BaseModel):
    """Target evidence required for an answer to be validly grounded."""
    document_id: str
    target_pages: List[int]
    target_section: Optional[str] = None
    target_blocks: Optional[List[str]] = None
    key_phrases: List[str]


class BenchmarkQuestion(BaseModel):
    """Single gold-standard benchmark item for evaluation."""
    question_id: str
    category: QuestionCategory
    reasoning_type: ReasoningType
    difficulty: DifficultyLevel
    target_documents: List[str]
    question: str
    expected_answer: str
    acceptable_variants: List[str] = Field(default_factory=list)
    is_answerable: bool = True
    unanswerable_reason: Optional[str] = None
    evidence_requirements: List[ExpectedEvidence]
    notes: Optional[str] = None
