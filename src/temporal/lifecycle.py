"""Contract Lifecycle Event Engine for ContractLens (Phase 9).

Extracts and registers deterministic lifecycle milestones (effective dates, expirations,
renewals, notice cutoffs, payment deadlines) with mandatory provenance pointers.
"""

from typing import List, Optional, Dict, Any
from src.models.canonical import CanonicalDocument, EvidenceReference
from src.models.intelligence import ContractIntelligence
from src.models.obligation import LifecycleEvent, LifecycleEventType, ContractObligation


class LifecycleEventEngine:
    """Extracts and maintains contractual lifecycle milestones and timeline events."""

    @staticmethod
    def generate_lifecycle_events(
        doc: CanonicalDocument,
        intelligence: ContractIntelligence,
        obligations: Optional[List[ContractObligation]] = None
    ) -> List[LifecycleEvent]:
        """Synthesize timeline lifecycle milestones from contract intelligence and obligations."""
        events: List[LifecycleEvent] = []
        event_counter = 1

        # 1. Effective Date Milestone
        if intelligence.effective_date.is_found and intelligence.effective_date.normalized_value:
            norm_val = intelligence.effective_date.normalized_value
            ev = intelligence.effective_date.evidence or LifecycleEventEngine._fallback_doc_evidence(doc)
            events.append(LifecycleEvent(
                event_id=f"evt_{doc.document_id}_{event_counter:03d}",
                event_type=LifecycleEventType.EFFECTIVE_DATE,
                title="Contract Effective Date",
                description=f"Agreement takes legal effect on {norm_val}.",
                date_or_trigger=norm_val,
                is_fixed_date=True,
                evidence=ev,
                metadata={"raw_text": intelligence.effective_date.raw_value or ""}
            ))
            event_counter += 1

        # 2. Expiration Date Milestone
        if intelligence.expiration_date.is_found and intelligence.expiration_date.normalized_value:
            norm_val = intelligence.expiration_date.normalized_value
            ev = intelligence.expiration_date.evidence or LifecycleEventEngine._fallback_doc_evidence(doc)
            events.append(LifecycleEvent(
                event_id=f"evt_{doc.document_id}_{event_counter:03d}",
                event_type=LifecycleEventType.EXPIRATION,
                title="Contract Initial Expiration",
                description=f"Agreement term expires on {norm_val} unless renewed or earlier terminated.",
                date_or_trigger=norm_val,
                is_fixed_date=True,
                evidence=ev,
                metadata={"raw_text": intelligence.expiration_date.raw_value or ""}
            ))
            event_counter += 1

        # 3. Renewal Language Milestone / Deadline
        if intelligence.renewal_language.is_found and intelligence.renewal_language.raw_value:
            ev = intelligence.renewal_language.evidence or LifecycleEventEngine._fallback_doc_evidence(doc)
            events.append(LifecycleEvent(
                event_id=f"evt_{doc.document_id}_{event_counter:03d}",
                event_type=LifecycleEventType.RENEWAL,
                title="Renewal Milestone / Notice Window",
                description=f"Contract renewal terms: {intelligence.renewal_language.raw_value[:150]}",
                date_or_trigger=intelligence.renewal_language.raw_value[:100],
                is_fixed_date=False,
                evidence=ev,
                metadata={"full_text": intelligence.renewal_language.raw_value}
            ))
            event_counter += 1

        # 4. Termination Notice Window Milestone
        if intelligence.termination_notice and intelligence.termination_notice.is_found and intelligence.termination_notice.normalized_value:
            tn = intelligence.termination_notice.normalized_value
            ev = tn.evidence or LifecycleEventEngine._fallback_doc_evidence(doc)
            events.append(LifecycleEvent(
                event_id=f"evt_{doc.document_id}_{event_counter:03d}",
                event_type=LifecycleEventType.NOTICE_DEADLINE,
                title="Termination Notice Deadline Window",
                description=f"Requires {tn.notice_days} days advance written notice for termination for {tn.termination_type.lower()}.",
                date_or_trigger=f"{tn.notice_days} days prior notice",
                is_fixed_date=False,
                evidence=ev,
                metadata={"notice_days": tn.notice_days, "termination_type": tn.termination_type}
            ))
            event_counter += 1

        # 5. Payment Due / Cycle Milestones
        if intelligence.payment_terms and intelligence.payment_terms.is_found and intelligence.payment_terms.normalized_value:
            pt = intelligence.payment_terms.normalized_value
            ev = pt.evidence or LifecycleEventEngine._fallback_doc_evidence(doc)
            events.append(LifecycleEvent(
                event_id=f"evt_{doc.document_id}_{event_counter:03d}",
                event_type=LifecycleEventType.PAYMENT_DEADLINE,
                title="Standard Payment Due Window",
                description=f"Payment is due {pt.payment_days} days following invoice receipt ({pt.payment_type}).",
                date_or_trigger=f"Invoice received + {pt.payment_days} days" if pt.payment_days else pt.payment_type,
                is_fixed_date=False,
                evidence=ev,
                metadata={"payment_days": pt.payment_days, "payment_type": pt.payment_type}
            ))
            event_counter += 1

        # 6. Amendment Milestones
        for af in intelligence.amendment_facts:
            events.append(LifecycleEvent(
                event_id=f"evt_{doc.document_id}_{event_counter:03d}",
                event_type=LifecycleEventType.AMENDMENT_EFFECTIVE_DATE,
                title=f"Amendment Modification: {af.target_section}",
                description=f"{af.action}: {af.summary}",
                date_or_trigger=af.action,
                is_fixed_date=False,
                evidence=af.evidence,
                metadata={"target_section": af.target_section, "raw_text": af.raw_text}
            ))
            event_counter += 1

        # 7. Add milestones from extracted obligations (e.g. recurring reporting)
        if obligations:
            for ob in obligations:
                if ob.temporal.temporal_type.value == "RECURRING":
                    events.append(LifecycleEvent(
                        event_id=f"evt_{doc.document_id}_{event_counter:03d}",
                        event_type=LifecycleEventType.RECURRING_OBLIGATION,
                        title=f"Recurring Obligation: {ob.action[:50]}",
                        description=f"{ob.actor} shall {ob.action} ({ob.temporal.recurrence.frequency.value if ob.temporal.recurrence else 'recurring'}).",
                        date_or_trigger=ob.temporal.raw_expression,
                        is_fixed_date=False,
                        evidence=ob.evidence,
                        associated_obligation_id=ob.obligation_id,
                        metadata={"actor": ob.actor, "action": ob.action}
                    ))
                    event_counter += 1

        return events

    @staticmethod
    def _fallback_doc_evidence(doc: CanonicalDocument) -> EvidenceReference:
        first_page = doc.pages[0] if doc.pages else None
        first_block = first_page.blocks[0] if first_page and first_page.blocks else None
        bbox = first_block.bbox if first_block else None
        from src.models.canonical import BoundingBox
        return EvidenceReference(
            document_id=doc.document_id,
            filename=doc.filename,
            page_number=1,
            block_id=first_block.block_id if first_block else "b_000",
            bbox=bbox or BoundingBox(x0=0.0, y0=0.0, x1=0.0, y1=0.0)
        )
