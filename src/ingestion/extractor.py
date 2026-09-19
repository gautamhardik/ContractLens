"""Deterministic and hybrid extraction engine for ContractIntelligence.

Extracts contract facts (parties, dates, payment terms, governing law,
termination notices, amendment modifications) directly from CanonicalDocument
blocks with strict provenance preservation.
"""

import re
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any

from src.models.canonical import CanonicalDocument, CanonicalBlock, BlockType
from src.models.intelligence import (
    ExtractionMethod,
    CandidateStatus,
    ExtractedField,
    ConflictedField,
    ContractParty,
    PaymentTerms,
    TerminationNotice,
    AmendmentFact,
    ContractIntelligence,
)


class ContractIntelligenceExtractor:
    """Extracts structured intelligence from CanonicalDocument blocks."""

    # Date regex patterns (e.g., June 1, 2005, October 6, 2015, 31 March 2026, 2025-02-24)
    DATE_PATTERNS = [
        re.compile(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b', re.IGNORECASE),
        re.compile(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+day\s+of\s+(January|February|March|April|May|June|July|August|September|October|November|December),?\s+(\d{4})\b', re.IGNORECASE),
        re.compile(r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b', re.IGNORECASE),
        re.compile(r'\b(\d{4})-(\d{2})-(\d{2})\b')
    ]

    # Effective date cues
    EFFECTIVE_DATE_CUES = re.compile(
        r'(effective\s+(?:as\s+of|date|as\s+at)\s*(?:is|:)?\s*|entered\s+into\s+(?:as\s+of|on)\s*(?:this)?\s*|dated\s+(?:as\s+of)?\s*)',
        re.IGNORECASE
    )

    # Expiration / Term cues
    EXPIRATION_CUES = re.compile(
        r'(shall\s+(?:expire|terminate|continue\s+until)|expiration\s+date|term\s+shall\s+end\s+on)\s*',
        re.IGNORECASE
    )

    # Governing law cues
    GOVERNING_LAW_CUES = re.compile(
        r'(?:governed\s+by[^\.\;]{1,80}?(?:laws\s+of\s+)?(?:the\s+State\s+of\s+|the\s+Commonwealth\s+of\s+|the\s+Province\s+of\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?))',
        re.IGNORECASE
    )

    # Payment term cues
    NET_PAYMENT_CUES = re.compile(
        r'\b(?:within|payable\s+within|net)\s+(thirty|forty-five|sixty|ninety|\d{1,3})\s*(?:\((\d{1,3})\))?\s*(?:calendar\s+)?days?\b',
        re.IGNORECASE
    )

    # Termination notice cues
    TERMINATION_NOTICE_CUES = re.compile(
        r'\b(?:written\s+notice\s+of|prior\s+written\s+notice\s+of|at\s+least)\s+(thirty|forty-five|sixty|ninety|\d{1,3})\s*(?:\((\d{1,3})\))?\s*(?:calendar\s+)?days?\b',
        re.IGNORECASE
    )

    WORD_TO_NUM = {
        "thirty": 30,
        "forty-five": 45,
        "sixty": 60,
        "ninety": 90,
        "fifteen": 15,
        "ten": 10
    }

    def extract(self, doc: CanonicalDocument) -> ContractIntelligence:
        """Runs full extraction pipeline on the canonical document."""
        clean_blocks = doc.get_all_blocks(include_noise=False)

        parties = self._extract_parties(doc, clean_blocks)
        effective_date = self._extract_effective_date(doc, clean_blocks)
        expiration_date = self._extract_expiration_date(doc, clean_blocks)
        renewal = self._extract_renewal_language(doc, clean_blocks)
        governing_law = self._extract_governing_law(doc, clean_blocks)
        payment_terms = self._extract_payment_terms(doc, clean_blocks)
        termination_notice = self._extract_termination_notice(doc, clean_blocks)
        amendment_facts = self._extract_amendment_facts(doc, clean_blocks)
        referenced_schedules = self._extract_referenced_schedules(clean_blocks)

        contract_type = self._classify_contract_type(doc)

        return ContractIntelligence(
            document_id=doc.document_id,
            filename=doc.filename,
            contract_type=contract_type,
            effective_date=effective_date,
            expiration_date=expiration_date,
            renewal_language=renewal,
            governing_law=governing_law,
            parties=parties,
            payment_terms=payment_terms,
            termination_notice=termination_notice,
            amendment_facts=amendment_facts,
            referenced_schedules=referenced_schedules,
            conflicts={},
            extraction_timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"total_clean_blocks": len(clean_blocks)}
        )

    def _classify_contract_type(self, doc: CanonicalDocument) -> ExtractedField[str]:
        """Classifies document archetype with provenance."""
        first_page_blocks = [b for b in doc.pages[0].blocks if not b.is_sec_noise] if doc.pages else []
        combined_header = " ".join([b.normalized_text for b in first_page_blocks[:5]])

        patterns = [
            (r'AMENDMENT\s+TO\s+MASTER\s+SERVICES\s+AGREEMENT|FIRST\s+AMENDMENT|AMENDMENT\s+CW', "Amendment"),
            (r'AMENDED\s+AND\s+RESTATED\s+MASTER\s+SERVICES\s+AGREEMENT', "Amended & Restated Master Services Agreement"),
            (r'MASTER\s+SERVICES\s+AGREEMENT|MASTER\s+SERVICE\s+AGREEMENT', "Master Services Agreement"),
            (r'SUPPLY\s+AGREEMENT|MASTER\s+SUPPLY\s+AGREEMENT', "Supply Agreement"),
            (r'SOFTWARE\s+LICENSE\s+AGREEMENT', "Software License Agreement"),
            (r'NON-DISCLOSURE\s+AGREEMENT|MUTUAL\s+NONDISCLOSURE\s+AGREEMENT', "Non-Disclosure Agreement"),
            (r'DATA\s+PROCESSING\s+AGREEMENT|EXCLUSIVE\s+LICENSE\s+AGREEMENT', "Exclusive License / DPA Provisions"),
            (r'STANDARD\s+SERVICES\s+AGREEMENT', "Standard Services Agreement + SOW"),
            (r'PROCESSING\s+AGREEMENT', "Processing Agreement")
        ]

        for pat, cat in patterns:
            for b in first_page_blocks[:6]:
                if re.search(pat, b.normalized_text, re.IGNORECASE):
                    return ExtractedField[str](
                        field_name="contract_type",
                        raw_value=b.normalized_text[:80],
                        normalized_value=cat,
                        confidence=0.95,
                        extraction_method=ExtractionMethod.DETERMINISTIC_REGEX,
                        evidence=b.to_evidence_ref(doc.filename),
                        is_found=True
                    )

        return ExtractedField[str].not_found("contract_type", "Archetype not detected on title blocks")

    def _extract_effective_date(self, doc: CanonicalDocument, blocks: List[CanonicalBlock]) -> ExtractedField[str]:
        """Extracts effective date looking at first 2 pages."""
        target_blocks = [b for b in blocks if b.page_number <= 2]

        for b in target_blocks:
            t = b.normalized_text
            # Check for direct date patterns on preamble blocks
            cue_match = self.EFFECTIVE_DATE_CUES.search(t)
            if cue_match:
                # Search across whole block if cue is present
                for p in self.DATE_PATTERNS:
                    d_match = p.search(t)
                    if d_match:
                        raw_date_str = d_match.group(0)
                        return ExtractedField[str](
                            field_name="effective_date",
                            raw_value=raw_date_str,
                            normalized_value=raw_date_str,
                            confidence=0.92,
                            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX,
                            evidence=b.to_evidence_ref(doc.filename),
                            is_found=True
                        )

        return ExtractedField[str].not_found("effective_date")

    def _extract_expiration_date(self, doc: CanonicalDocument, blocks: List[CanonicalBlock]) -> ExtractedField[str]:
        """Extracts expiration / end date."""
        for b in blocks:
            if b.section_title and any(k in b.section_title.lower() for k in ["term", "expiration"]):
                cue_match = self.EXPIRATION_CUES.search(b.normalized_text)
                if cue_match:
                    for p in self.DATE_PATTERNS:
                        d_match = p.search(b.normalized_text)
                        if d_match:
                            raw_d = d_match.group(0)
                            return ExtractedField[str](
                                field_name="expiration_date",
                                raw_value=raw_d,
                                normalized_value=raw_d,
                                confidence=0.85,
                                extraction_method=ExtractionMethod.DETERMINISTIC_REGEX,
                                evidence=b.to_evidence_ref(doc.filename),
                                is_found=True
                            )

        return ExtractedField[str].not_found("expiration_date", "No fixed calendar expiration date identified")

    def _extract_renewal_language(self, doc: CanonicalDocument, blocks: List[CanonicalBlock]) -> ExtractedField[str]:
        """Extracts renewal conditions or automatic extension clauses."""
        for b in blocks:
            if any(k in b.normalized_text.lower() for k in ["automatically renew", "automatic renewal", "successive terms", "consecutive terms", "renewal term"]):
                return ExtractedField[str](
                    field_name="renewal_language",
                    raw_value=b.normalized_text[:120],
                    normalized_value="Automatic / Successive Renewal Detected",
                    confidence=0.90,
                    extraction_method=ExtractionMethod.DETERMINISTIC_REGEX,
                    evidence=b.to_evidence_ref(doc.filename),
                    is_found=True
                )

        return ExtractedField[str].not_found("renewal_language")

    def _extract_governing_law(self, doc: CanonicalDocument, blocks: List[CanonicalBlock]) -> ExtractedField[str]:
        """Extracts governing law jurisdiction."""
        # Typically in later sections
        for b in reversed(blocks):
            if any(k in b.normalized_text.lower() for k in ["governed by", "governing law", "jurisdiction", "laws of the state of"]):
                m = self.GOVERNING_LAW_CUES.search(b.normalized_text)
                if m:
                    state = m.group(1).strip()
                    # Filter out common false positives
                    if state.lower() not in ["this", "such", "the", "any", "which"]:
                        return ExtractedField[str](
                            field_name="governing_law",
                            raw_value=m.group(0),
                            normalized_value=state,
                            confidence=0.88,
                            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX,
                            evidence=b.to_evidence_ref(doc.filename),
                            is_found=True
                        )

        return ExtractedField[str].not_found("governing_law")

    def _extract_payment_terms(self, doc: CanonicalDocument, blocks: List[CanonicalBlock]) -> ExtractedField[PaymentTerms]:
        """Extracts payment term days (e.g. Net 30, within 30 days of receipt)."""
        for b in blocks:
            if any(k in b.normalized_text.lower() for k in ["invoice", "payable", "payment", "net 30", "net 45", "net 60"]):
                m = self.NET_PAYMENT_CUES.search(b.normalized_text)
                if m:
                    val_str = m.group(2) or m.group(1)
                    num_days = self._parse_num_days(val_str)
                    if num_days:
                        payment_obj = PaymentTerms(
                            payment_type=f"Net {num_days}" if num_days else "Custom",
                            payment_days=num_days,
                            raw_text=m.group(0),
                            evidence=b.to_evidence_ref(doc.filename)
                        )
                        return ExtractedField[PaymentTerms](
                            field_name="payment_terms",
                            raw_value=m.group(0),
                            normalized_value=payment_obj,
                            confidence=0.90,
                            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX,
                            evidence=b.to_evidence_ref(doc.filename),
                            is_found=True
                        )

        return ExtractedField[PaymentTerms].not_found("payment_terms")

    def _extract_termination_notice(self, doc: CanonicalDocument, blocks: List[CanonicalBlock]) -> ExtractedField[TerminationNotice]:
        """Extracts termination notice period in days."""
        for b in blocks:
            if any(k in b.normalized_text.lower() for k in ["termination", "terminate"]):
                m = self.TERMINATION_NOTICE_CUES.search(b.normalized_text)
                if m:
                    val_str = m.group(2) or m.group(1)
                    num_days = self._parse_num_days(val_str)
                    if num_days:
                        term_type = "Convenience" if "convenience" in b.normalized_text.lower() else "Standard / Breach"
                        notice_obj = TerminationNotice(
                            notice_days=num_days,
                            termination_type=term_type,
                            raw_text=m.group(0),
                            evidence=b.to_evidence_ref(doc.filename)
                        )
                        return ExtractedField[TerminationNotice](
                            field_name="termination_notice",
                            raw_value=m.group(0),
                            normalized_value=notice_obj,
                            confidence=0.88,
                            extraction_method=ExtractionMethod.DETERMINISTIC_REGEX,
                            evidence=b.to_evidence_ref(doc.filename),
                            is_found=True
                        )

        return ExtractedField[TerminationNotice].not_found("termination_notice")

    def _extract_parties(self, doc: CanonicalDocument, blocks: List[CanonicalBlock]) -> List[ContractParty]:
        """Extracts contracting parties from Preamble or Signature blocks."""
        parties: List[ContractParty] = []
        preamble_blocks = [b for b in blocks if b.page_number <= 2]

        # Look for "between X and Y" or "by and among X and Y"
        for b in preamble_blocks:
            t = b.normalized_text
            m = re.search(r'(?:by\s+and\s+between|between|by\s+and\s+among)\s+([A-Z0-9\.,\s\(\)\'\-]+?)\s+(?:and|,)\s+([A-Z0-9\.,\s\(\)\'\-]+?)(?:\s*\(|\s+RECITALS|\s+WHEREAS|\.$)', t)
            if m:
                p1_raw = m.group(1).strip()
                p2_raw = m.group(2).strip()
                p1_clean = self._clean_party_name(p1_raw)
                p2_clean = self._clean_party_name(p2_raw)

                if p1_clean:
                    parties.append(ContractParty(
                        name=p1_clean,
                        raw_text=p1_raw[:100],
                        evidence=b.to_evidence_ref(doc.filename)
                    ))
                if p2_clean:
                    parties.append(ContractParty(
                        name=p2_clean,
                        raw_text=p2_raw[:100],
                        evidence=b.to_evidence_ref(doc.filename)
                    ))
                break

        return parties

    def _extract_amendment_facts(self, doc: CanonicalDocument, blocks: List[CanonicalBlock]) -> List[AmendmentFact]:
        """Extracts declared modifications if the document is an amendment."""
        facts: List[AmendmentFact] = []

        for b in blocks:
            t = b.normalized_text
            # Check delete and replace
            m_del = re.search(r'(Section\s+[0-9\.]+)\s+of\s+the\s+Agreement\s+shall\s+be\s+deleted\s+in\s+its\s+entirety\s+and\s+the\s+following\s+shall\s+be\s+inserted', t, re.IGNORECASE)
            if m_del:
                sec = m_del.group(1)
                facts.append(AmendmentFact(
                    action="DELETE_AND_REPLACE",
                    target_section=sec,
                    summary=f"Replaces {sec} in its entirety.",
                    raw_text=t[:120],
                    evidence=b.to_evidence_ref(doc.filename)
                ))
            # Check additions (e.g. insurance)
            m_add = re.search(r'(Section\s+[0-9\.]+)\s+of\s+the\s+Agreement\s+shall\s+be\s+amended\s+by\s+adding\s+the\s+following\s+insurance\s+coverage', t, re.IGNORECASE)
            if m_add:
                sec = m_add.group(1)
                facts.append(AmendmentFact(
                    action="ADD_COVERAGE",
                    target_section=sec,
                    summary=f"Adds insurance coverage requirement to {sec}.",
                    raw_text=t[:120],
                    evidence=b.to_evidence_ref(doc.filename)
                ))
            # Check full force confirmation
            m_force = re.search(r'remain\s+in\s+full\s+force\s+and\s+effect', t, re.IGNORECASE)
            if m_force:
                facts.append(AmendmentFact(
                    action="CONFIRM_FULL_FORCE",
                    target_section="General",
                    summary="Confirms unamended provisions of base agreement remain in full force and effect.",
                    raw_text=t[:120],
                    evidence=b.to_evidence_ref(doc.filename)
                ))

        return facts

    def _extract_referenced_schedules(self, blocks: List[CanonicalBlock]) -> List[str]:
        """Collects referenced schedules, exhibits, and appendices."""
        schedules = set()
        pat = re.compile(r'\b(Exhibit\s+[A-Z0-9\.]+|Schedule\s+[A-Z0-9\.]+|Appendix\s+[A-Z0-9\.]+)\b', re.IGNORECASE)
        for b in blocks:
            for match in pat.findall(b.normalized_text):
                schedules.add(match.title())
        return sorted(list(schedules))[:10]  # Top 10

    def _clean_party_name(self, raw: str) -> Optional[str]:
        """Cleans and isolates corporate entity names."""
        clean = raw.strip()
        # Cut off after corporate suffixes
        m = re.search(r'(.*?,\s*(?:Inc\.|LLC|Corp\.|Corporation|Co\.|Ltd\.|Pty\s+Ltd|L\.P\.|N\.A\.))', clean, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        if len(clean) < 60 and not clean.startswith("this"):
            return clean
        return None

    def _parse_num_days(self, val_str: str) -> Optional[int]:
        """Normalizes day representations into integer."""
        val_clean = val_str.strip().lower()
        if val_clean.isdigit():
            return int(val_clean)
        return self.WORD_TO_NUM.get(val_clean, None)
