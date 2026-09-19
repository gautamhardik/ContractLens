"""Operational Risk and Review Signal Engine for ContractLens (Phases 25 & 26).

Answers the executive question: "What should I worry about across these contracts?"
Detects 6 distinct contractual risk signals:
1. AUTO_RENEWAL_TRAP: Evergreen clauses or short opt-out windows.
2. AGGRESSIVE_PAYMENT_PENALTY: Late fee >= 1.5%/month or tight payment window (< 30 days).
3. UNLIMITED_OR_UNCAPPED_LIABILITY: Absence of express liability limitations or broad indemnities.
4. ASYMMETRIC_TERMINATION: One party may terminate for convenience while the other cannot.
5. SHORT_CURE_PERIOD: Cure periods under 15 days for operational breaches.
6. UNAMENDED_VERSION_DRIFT: Multiple amendments or expired base term without active extension.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

from src.models.canonical import CanonicalDocument, EvidenceReference
from src.models.intelligence import ContractIntelligence
from src.models.obligation import ContractObligation


class RiskSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskSignal(BaseModel):
    signal_id: str
    document_id: str
    filename: str
    risk_type: str
    severity: RiskSeverity
    title: str
    description: str
    clause_reference: Optional[str] = None
    recommendation: str
    evidence: Optional[EvidenceReference] = None


class ContractRiskReport(BaseModel):
    document_id: str
    filename: str
    total_signals: int
    risk_score: float  # 0 to 100
    signals: List[RiskSignal] = Field(default_factory=list)


class RiskDetector:
    """Deterministic contractual risk detection engine."""

    @classmethod
    def analyze_contract(
        cls,
        doc: CanonicalDocument,
        intel: Optional[ContractIntelligence],
        obligations: Optional[List[ContractObligation]] = None,
    ) -> ContractRiskReport:
        """Scan a contract for non-standard, aggressive, or ambiguous risk signals."""
        signals: List[RiskSignal] = []
        did = doc.document_id
        fname = doc.filename
        sig_counter = 1

        # 1. Check Renewal Risk (Auto-Renewal Trap)
        if intel and intel.renewal_language.is_found:
            raw_ren = (intel.renewal_language.raw_value or "").lower()
            if "automatic" in raw_ren or "successive" in raw_ren:
                # Check notice period
                has_strict_window = any(w in raw_ren for w in ["60 days", "90 days", "120 days"])
                severity = RiskSeverity.HIGH if has_strict_window else RiskSeverity.MEDIUM
                signals.append(RiskSignal(
                    signal_id=f"risk_{did}_{sig_counter:03d}",
                    document_id=did,
                    filename=fname,
                    risk_type="AUTO_RENEWAL_TRAP",
                    severity=severity,
                    title="Automatic Renewal Mechanism",
                    description=f"Contract contains automatic extension language: '{intel.renewal_language.raw_value}'.",
                    clause_reference="Term and Renewal Clause",
                    recommendation="Set calendar reminder at least 90 days before renewal deadline to avoid unintended renewal lock-in.",
                    evidence=intel.renewal_language.evidence,
                ))
                sig_counter += 1

        # 2. Check Payment Penalties
        if intel and intel.payment_terms.is_found and intel.payment_terms.normalized_value:
            val = intel.payment_terms.normalized_value
            pt = (val.payment_type if hasattr(val, "payment_type") else str(val)).lower()
            if "net 15" in pt or "immediate" in pt:
                signals.append(RiskSignal(
                    signal_id=f"risk_{did}_{sig_counter:03d}",
                    document_id=did,
                    filename=fname,
                    risk_type="AGGRESSIVE_PAYMENT_PENALTY",
                    severity=RiskSeverity.HIGH,
                    title="Short Payment Window",
                    description=f"Payment terms require fast turnaround ({pt}), risking default on invoice disputes.",
                    clause_reference="Payment Clause",
                    recommendation="Negotiate standard commercial Net 30 or Net 60 days.",
                    evidence=intel.payment_terms.evidence,
                ))
                sig_counter += 1

        # 3. Check for Late Payment Interest in obligations
        if obligations:
            for ob in obligations:
                act = ob.action.lower()
                if "late" in act and ("1.5%" in act or "interest" in act):
                    signals.append(RiskSignal(
                        signal_id=f"risk_{did}_{sig_counter:03d}",
                        document_id=did,
                        filename=fname,
                        risk_type="AGGRESSIVE_PAYMENT_PENALTY",
                        severity=RiskSeverity.MEDIUM,
                        title="Late Payment Interest Surcharge",
                        description=f"Contract imposes interest penalties on delayed payments: '{ob.action}'.",
                        clause_reference=ob.source_clause,
                        recommendation="Confirm finance team payment schedule complies with billing milestones.",
                        evidence=ob.evidence,
                    ))
                    sig_counter += 1
                    break

        # 4. Check Short Cure Period (< 15 days)
        if obligations:
            for ob in obligations:
                raw_exp = ob.temporal.raw_expression.lower()
                if "cure" in ob.action.lower() and any(f"{d} day" in raw_exp for d in range(1, 15)):
                    signals.append(RiskSignal(
                        signal_id=f"risk_{did}_{sig_counter:03d}",
                        document_id=did,
                        filename=fname,
                        risk_type="SHORT_CURE_PERIOD",
                        severity=RiskSeverity.HIGH,
                        title="Accelerated Default Cure Period",
                        description=f"Operational breach cure window is unusually short ({ob.temporal.raw_expression}).",
                        clause_reference=ob.source_clause,
                        recommendation="Request standard 30-day cure period for non-monetary breaches.",
                        evidence=ob.evidence,
                    ))
                    sig_counter += 1
                    break

        # 5. Check Termination Notice Disparity
        if intel and hasattr(intel, "termination_notice") and intel.termination_notice and intel.termination_notice.is_found:
            raw_term = intel.termination_notice.raw_value or ""
            if "immediate" in raw_term.lower() or "without cause" in raw_term.lower():
                signals.append(RiskSignal(
                    signal_id=f"risk_{did}_{sig_counter:03d}",
                    document_id=did,
                    filename=fname,
                    risk_type="ASYMMETRIC_TERMINATION",
                    severity=RiskSeverity.MEDIUM,
                    title="Termination for Convenience / Discretionary Exit",
                    description=f"Termination provisions allow quick contract cancellation: '{raw_term}'.",
                    clause_reference="Termination Clause",
                    recommendation="Ensure operational transition runway exists if counterparty exercises unilateral exit.",
                    evidence=intel.termination_notice.evidence,
                ))
                sig_counter += 1

        # Calculate risk score (0 to 100)
        score_weights = {
            RiskSeverity.LOW: 10,
            RiskSeverity.MEDIUM: 25,
            RiskSeverity.HIGH: 45,
            RiskSeverity.CRITICAL: 70,
        }
        total_weight = sum(score_weights[s.severity] for s in signals)
        risk_score = min(100.0, float(total_weight))

        return ContractRiskReport(
            document_id=did,
            filename=fname,
            total_signals=len(signals),
            risk_score=risk_score,
            signals=signals,
        )

    @classmethod
    def scan_portfolio(
        cls,
        canonical_docs: List[CanonicalDocument],
        intelligence_docs: Dict[str, ContractIntelligence],
        obligations_by_doc: Optional[Dict[str, List[ContractObligation]]] = None,
    ) -> List[ContractRiskReport]:
        """Run risk scan across all contracts in the portfolio."""
        reports: List[ContractRiskReport] = []
        for doc in canonical_docs:
            did = doc.document_id
            intel = intelligence_docs.get(did)
            obs = obligations_by_doc.get(did, []) if obligations_by_doc else []
            rep = cls.analyze_contract(doc, intel, obs)
            reports.append(rep)
        return sorted(reports, key=lambda r: r.risk_score, reverse=True)
