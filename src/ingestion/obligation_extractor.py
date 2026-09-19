"""Deterministic and hybrid obligation extractor for ContractLens (Phase 7).

Identifies candidate obligation clauses using modal triggers, section semantics,
and contractual covenants. Resolves actors to parties (or keeps unresolved),
normalizes temporal expressions, and attaches exact evidence provenance.
"""

import re
from typing import List, Optional, Dict, Any, Tuple

from src.models.canonical import CanonicalDocument, CanonicalBlock, BlockType, EvidenceReference
from src.models.intelligence import ContractIntelligence, ContractParty, ExtractionMethod
from src.models.obligation import (
    ContractObligation,
    ObligationStatus,
    TemporalConstraint,
    TemporalType,
)
from src.temporal.engine import TemporalEngine


# Modal verb patterns signalling contractual obligations
OBLIGATION_MODALS = re.compile(
    r"\b(shall\s+not|shall|must\s+not|must|agrees?\s+to|is\s+required\s+to|responsible\s+for|will\s+not|will\s+maintain|will\s+pay|will\s+provide)\b",
    re.IGNORECASE
)

# Common contract section types where key obligations reside
OBLIGATION_SECTION_KEYWORDS = [
    "payment", "fee", "compensation", "invoice", "taxes",
    "term", "termination", "expiration", "renewal",
    "insurance", "liability", "indemnification",
    "reporting", "records", "audit", "delivery", "warranty",
    "confidentiality", "security", "data protection", "covenants"
]


class ObligationExtractor:
    """Extracts strongly-typed ContractObligation records with mandatory provenance."""

    def __init__(self):
        self.temporal_engine = TemporalEngine()

    def extract_obligations(
        self,
        doc: CanonicalDocument,
        intelligence: Optional[ContractIntelligence] = None
    ) -> List[ContractObligation]:
        """Extract all candidate obligations across the CanonicalDocument."""
        obligations: List[ContractObligation] = []
        ob_counter = 1

        parties = intelligence.parties if intelligence else []

        for page in doc.pages:
            for block in page.blocks:
                # Skip SEC headers/footers/noise
                if block.block_type in (BlockType.PAGE_HEADER, BlockType.PAGE_FOOTER, BlockType.SEC_NOISE):
                    continue

                text = block.raw_text.strip()
                if not text or len(text) < 15:
                    continue

                # Check if block has modal signals
                if not OBLIGATION_MODALS.search(text):
                    continue

                # Split complex sentences / list items into obligation candidates
                sentences = self._split_into_obligation_units(text)

                for sent in sentences:
                    modal_match = OBLIGATION_MODALS.search(sent)
                    if not modal_match:
                        continue

                    # Actor resolution
                    actor, actor_role, counterparty = self._resolve_actors(sent, parties)

                    # Action and object/scope extraction
                    action, obj_scope = self._extract_action_and_scope(sent, modal_match)

                    # Temporal constraint extraction
                    temporal = self.temporal_engine.parse_temporal_expression(sent)

                    # Clause identifier
                    source_clause = block.section_title or f"Page {page.page_number} Block {block.block_id}"

                    ev = EvidenceReference(
                        document_id=doc.document_id,
                        filename=doc.filename,
                        page_number=page.page_number,
                        block_id=block.block_id,
                        bbox=block.bbox,
                        section_title=block.section_title,
                        char_offset_start=0,
                        char_offset_end=len(sent)
                    )

                    ob = ContractObligation(
                        obligation_id=f"obl_{doc.document_id}_{ob_counter:03d}",
                        actor=actor,
                        actor_role=actor_role,
                        counterparty=counterparty,
                        action=action,
                        object_or_scope=obj_scope,
                        temporal=temporal,
                        status=ObligationStatus.UNKNOWN,  # Do not invent completion status!
                        source_clause=source_clause,
                        evidence=ev,
                        extraction_method=ExtractionMethod.DETERMINISTIC_HEURISTIC,
                        confidence=0.90 if actor != "unresolved" else 0.75
                    )
                    obligations.append(ob)
                    ob_counter += 1

        return obligations

    def _split_into_obligation_units(self, text: str) -> List[str]:
        """Split text by semicolons or sentence boundaries if multiple obligations exist."""
        # Check if semicolon separated list (common in legal contracts)
        if ";" in text and OBLIGATION_MODALS.search(text):
            parts = [p.strip() for p in text.split(";") if len(p.strip()) > 15]
            if len(parts) > 1:
                return parts

        # Standard sentence split
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9\(\)])', text)
        return [s.strip() for s in sentences if len(s.strip()) > 15]

    def _resolve_actors(
        self,
        sentence: str,
        parties: List[ContractParty]
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """Resolve actor and counterparty from text and identified parties.

        If ambiguous or unknown, returns 'unresolved' (DO NOT GUESS).
        """
        lower = sentence.lower()

        # Check identified party names first
        for p in parties:
            p_name_lower = p.name.lower()
            # E.g. "Access", "E*TRADE", "Foxconn", "Turtle Beach", "HP", "Spare"
            short_name = p_name_lower.split()[0] if len(p_name_lower.split()) > 0 else p_name_lower
            if short_name in lower or p_name_lower in lower:
                # Found party
                counterparty = None
                for cp in parties:
                    if cp.name != p.name:
                        counterparty = cp.name
                        break
                return (p.name, p.role, counterparty)

        # Common contract roles
        role_map = {
            "vendor": "Vendor",
            "customer": "Customer",
            "supplier": "Supplier",
            "client": "Client",
            "licensor": "Licensor",
            "licensee": "Licensee",
            "buyer": "Buyer",
            "seller": "Seller",
            "contractor": "Contractor",
            "service provider": "Service Provider",
            "each party": "Each Party",
            "both parties": "Both Parties",
            "either party": "Either Party",
            "the parties": "The Parties"
        }

        # Look for leading subject or role before modal
        modal_match = OBLIGATION_MODALS.search(sentence)
        if modal_match:
            prefix = sentence[:modal_match.start()].strip().lower()
            for role_cue, role_name in role_map.items():
                if role_cue in prefix:
                    # Counterparty assignment
                    counterparty = "Counterparty" if "party" not in role_cue else None
                    return (role_name, role_name, counterparty)

        # Check anywhere in sentence for mutual
        if "each party" in lower or "the parties shall" in lower:
            return ("The Parties", "Mutual", None)

        # Ambiguous: return 'unresolved' per rule
        return ("unresolved", None, None)

    def _extract_action_and_scope(
        self,
        sentence: str,
        modal_match: re.Match
    ) -> Tuple[str, Optional[str]]:
        """Extract the action verb phrase and the direct object or scope."""
        post_modal = sentence[modal_match.end():].strip()
        words = post_modal.split()

        if not words:
            return (modal_match.group(0), None)

        # Take first 4-8 words as core action phrase
        action_phrase = " ".join(words[:min(6, len(words))]).strip(",;.")
        obj_scope = " ".join(words[min(6, len(words)):min(16, len(words))]).strip(",;.") if len(words) > 6 else None

        full_action = f"{modal_match.group(0)} {action_phrase}"
        return (full_action, obj_scope if obj_scope else None)
