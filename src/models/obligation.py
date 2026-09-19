"""Contract Obligation Schema for ContractLens (Phase 7–9).

Defines strongly-typed models for operational contract commitments, temporal
constraints, recurrence rules, and lifecycle milestones with strict provenance.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.models.canonical import EvidenceReference
from src.models.intelligence import ExtractionMethod


class TemporalType(str, Enum):
    """Explicit contractual timing categories.

    Do NOT force all obligations into calendar dates.
    """
    FIXED_DATE = "FIXED_DATE"                # Concrete date stated (e.g. "June 30, 2027")
    RELATIVE_OFFSET = "RELATIVE_OFFSET"      # E.g. "Within 30 days of receipt"
    EVENT_RELATIVE = "EVENT_RELATIVE"        # E.g. "Within 10 days after discovering breach"
    RECURRING = "RECURRING"                  # E.g. "Monthly report", "Quarterly audit"
    CONDITIONAL = "CONDITIONAL"              # E.g. "If X occurs, party shall notify Y within 30 days"
    ONGOING = "ONGOING"                      # E.g. "Maintain insurance coverage throughout Term"
    UNSPECIFIED = "UNSPECIFIED"              # Obligation exists but no timing stated


class ObligationStatus(str, Enum):
    """Operational status of a contract commitment.

    CRITICAL RULE: Without external operational data, real-world completion status
    must remain UNKNOWN. Do not invent whether a company completed an obligation.
    """
    UPCOMING = "UPCOMING"
    DUE = "DUE"
    OVERDUE = "OVERDUE"
    COMPLETED = "COMPLETED"
    UNKNOWN = "UNKNOWN"


class RecurrenceFrequency(str, Enum):
    """Recurrence intervals for recurring obligations."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    EVENT_BASED = "event_based"
    CUSTOM = "custom"


class RecurrenceRule(BaseModel):
    """Specification of recurrence without premature infinite date instantiation."""
    frequency: RecurrenceFrequency
    interval: int = 1  # e.g., every 1 month, every 2 quarters
    anchor_description: Optional[str] = None  # e.g., "by the 15th day of each calendar month"
    custom_rule: Optional[str] = None


class TemporalConstraint(BaseModel):
    """Normalized temporal relationship for an obligation.

    Preserves raw expression and calculated dates separately.
    Does NOT invent anchor dates: if anchor is unknown, is_resolved=False.
    """
    temporal_type: TemporalType
    raw_expression: str
    offset_days: Optional[int] = None
    offset_months: Optional[int] = None
    anchor_event: Optional[str] = None  # E.g., "invoice_received", "breach_discovered", "effective_date"
    anchor_date: Optional[str] = None   # ISO format YYYY-MM-DD if explicitly provided/known
    calculated_date: Optional[str] = None  # Populated ONLY when anchor_date is available
    is_resolved: bool = False
    recurrence: Optional[RecurrenceRule] = None
    condition: Optional[str] = None     # Triggering condition if CONDITIONAL


class ContractObligation(BaseModel):
    """Strongly typed operational obligation extracted from contract clauses."""
    obligation_id: str
    actor: str                           # Resolved party or "unresolved" (Do NOT guess)
    actor_role: Optional[str] = None     # E.g., "Supplier", "Customer", "Licensee"
    counterparty: Optional[str] = None   # Beneficiary or recipient party
    action: str                          # Obligation verb phrase (e.g. "provide monthly reports", "pay invoice")
    object_or_scope: Optional[str] = None  # E.g., "written reports of service levels", "undisputed charges"
    temporal: TemporalConstraint
    status: ObligationStatus = ObligationStatus.UNKNOWN
    source_clause: str                   # E.g., "Section 6.1", "Paragraph 4"
    evidence: EvidenceReference          # Mandatory provenance pointer
    extraction_method: ExtractionMethod = ExtractionMethod.DETERMINISTIC_HEURISTIC
    confidence: float = 1.0


class LifecycleEventType(str, Enum):
    """Contractual lifecycle milestones."""
    EFFECTIVE_DATE = "effective_date"
    COMMENCEMENT = "commencement"
    EXPIRATION = "expiration"
    RENEWAL = "renewal"
    TERMINATION = "termination"
    NOTICE_DEADLINE = "notice_deadline"
    PAYMENT_DEADLINE = "payment_deadline"
    RECURRING_OBLIGATION = "recurring_obligation"
    AMENDMENT_EFFECTIVE_DATE = "amendment_effective_date"
    OTHER_MILESTONE = "other_milestone"


class LifecycleEvent(BaseModel):
    """Lifecycle event or milestone rooted in contract evidence."""
    event_id: str
    event_type: LifecycleEventType
    title: str
    description: str
    date_or_trigger: str                 # Fixed date string (YYYY-MM-DD) or triggering expression
    is_fixed_date: bool
    evidence: EvidenceReference
    associated_obligation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
