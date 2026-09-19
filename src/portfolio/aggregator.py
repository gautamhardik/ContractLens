"""Portfolio Intelligence and Cross-Contract Aggregator for ContractLens (Phases 23 & 24).

Aggregates structured metrics and contractual intelligence across all 18 corpus documents:
- Portfolio overview KPIs: total contracts, total counterparties, total obligations, total pages.
- Governing law distribution (e.g. Delaware, Texas, California, etc.).
- Payment term distribution (Net 30, Net 60, etc.).
- Expiration timeline & upcoming milestone calendar (next 30/60/90/180 days).
- Counterparty relationship matrix.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.canonical import CanonicalDocument, EvidenceReference
from src.models.intelligence import ContractIntelligence
from src.models.obligation import ContractObligation, LifecycleEvent, LifecycleEventType


class CounterpartySummary(BaseModel):
    name: str
    contract_count: int
    contract_ids: List[str]
    roles: List[str] = Field(default_factory=list)


class MilestoneSummary(BaseModel):
    event_id: str
    document_id: str
    filename: str
    event_type: str
    title: str
    date_or_trigger: str
    is_fixed_date: bool
    evidence: Optional[EvidenceReference] = None


class PortfolioOverview(BaseModel):
    total_contracts: int
    total_pages: int
    total_obligations: int
    total_events: int
    governing_laws: Dict[str, int]
    payment_terms: Dict[str, int]
    counterparties: List[CounterpartySummary]
    upcoming_milestones: List[MilestoneSummary]
    contracts_metadata: List[Dict[str, Any]]


class PortfolioAggregator:
    """Aggregates multi-contract metrics across the ContractLens corpus."""

    @classmethod
    def aggregate(
        cls,
        canonical_docs: List[CanonicalDocument],
        intelligence_docs: Dict[str, ContractIntelligence],
        obligations: List[ContractObligation],
        events: List[LifecycleEvent],
    ) -> PortfolioOverview:
        """Compute portfolio-level statistics with full provenance retention."""
        total_contracts = len(canonical_docs)
        total_pages = sum(d.page_count for d in canonical_docs)
        total_obligations = len(obligations)
        total_events = len(events)

        governing_laws: Dict[str, int] = {}
        payment_terms: Dict[str, int] = {}
        party_contracts: Dict[str, List[str]] = {}

        contracts_metadata: List[Dict[str, Any]] = []

        for doc in canonical_docs:
            did = doc.document_id
            intel = intelligence_docs.get(did)

            # Governing Law
            if intel and intel.governing_law.is_found and intel.governing_law.normalized_value:
                law = intel.governing_law.normalized_value
                governing_laws[law] = governing_laws.get(law, 0) + 1
            else:
                governing_laws["Unspecified"] = governing_laws.get("Unspecified", 0) + 1

            # Payment Terms
            if intel and intel.payment_terms.is_found and intel.payment_terms.normalized_value:
                val = intel.payment_terms.normalized_value
                pt_str = val.payment_type if hasattr(val, "payment_type") else str(val)
                payment_terms[pt_str] = payment_terms.get(pt_str, 0) + 1
            else:
                payment_terms["Standard / Unspecified"] = payment_terms.get("Standard / Unspecified", 0) + 1

            # Parties
            parties_list = []
            if intel and intel.parties:
                for p in intel.parties:
                    p_name = p.name.strip()
                    parties_list.append(p_name)
                    if p_name not in party_contracts:
                        party_contracts[p_name] = []
                    party_contracts[p_name].append(did)

            contracts_metadata.append({
                "document_id": did,
                "filename": doc.filename,
                "page_count": doc.page_count,
                "parties": parties_list,
                "governing_law": intel.governing_law.normalized_value if (intel and intel.governing_law.is_found) else "Unspecified",
                "payment_terms": intel.payment_terms.normalized_value if (intel and intel.payment_terms.is_found) else "Unspecified",
                "effective_date": intel.effective_date.normalized_value if (intel and intel.effective_date.is_found) else "Unspecified",
                "expiration_date": intel.expiration_date.normalized_value if (intel and intel.expiration_date.is_found) else "Unspecified",
                "has_amendments": bool(intel and intel.amendment_facts),
            })

        # Counterparties
        counterparties: List[CounterpartySummary] = [
            CounterpartySummary(
                name=name,
                contract_count=len(dids),
                contract_ids=dids,
            )
            for name, dids in sorted(party_contracts.items(), key=lambda x: len(x[1]), reverse=True)
        ]

        # Milestone Summaries
        milestones: List[MilestoneSummary] = []
        for ev in events:
            milestones.append(MilestoneSummary(
                event_id=ev.event_id,
                document_id=ev.evidence.document_id if ev.evidence else "unknown",
                filename=ev.evidence.filename if ev.evidence else "unknown",
                event_type=ev.event_type.value,
                title=ev.title,
                date_or_trigger=ev.date_or_trigger,
                is_fixed_date=ev.is_fixed_date,
                evidence=ev.evidence,
            ))

        return PortfolioOverview(
            total_contracts=total_contracts,
            total_pages=total_pages,
            total_obligations=total_obligations,
            total_events=total_events,
            governing_laws=governing_laws,
            payment_terms=payment_terms,
            counterparties=counterparties,
            upcoming_milestones=milestones,
            contracts_metadata=contracts_metadata,
        )
