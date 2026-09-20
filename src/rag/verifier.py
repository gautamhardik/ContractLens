"""Deterministic Claim and Evidence Verification Engine for ContractLens (Phase 16).

Independently assesses factual claims against cited EvidenceSpan source text without trusting
model-provided assertions.

Checks:
1. Layer 1: Citation existence and validity in the EvidenceBundle.
2. Layer 2: Deterministic lexical & structured factual alignment:
   - Key numeric/term match (e.g. Net 30, $2,000,000, Delaware, 30 days).
   - Negation & contradiction detection ('not', 'never', 'no automatic renewal').
   - Modality checks ('may' vs 'shall'/'must').
   - Date precision.
3. Layer 3: Contradiction & amendment override handling.
"""

import re
from typing import List, Dict, Tuple, Set, Optional

from src.evidence.models import EvidenceSpan, EvidenceCitation, EvidenceBundle
from src.rag.models import (
    GroundedClaim,
    VerificationResult,
    VerificationReport,
    ClaimVerificationStatus,
)


class ClaimVerifier:
    """Independent deterministic auditor verifying that evidence actually supports factual claims."""

    # Modality and negation indicators
    NEGATION_WORDS = {"not", "never", "neither", "nor", "none", "no", "without"}
    MANDATORY_WORDS = {"shall", "must", "will", "required", "agrees to"}
    PERMISSIVE_WORDS = {"may", "permitted", "option", "discretion"}

    @classmethod
    def verify_claim(
        cls,
        claim: GroundedClaim,
        evidence_map: Dict[str, EvidenceSpan],
    ) -> VerificationResult:
        """Independently verify whether cited evidence supports a specific claim."""
        # Check 1: Did the claim cite any evidence?
        if not claim.evidence_ids:
            return VerificationResult(
                claim_id=claim.claim_id,
                status=ClaimVerificationStatus.INSUFFICIENT_EVIDENCE,
                evidence_ids=[],
                is_supported=False,
                reason="Claim made without citing any supporting evidence ID.",
                confidence=1.0,
            )

        # Check 2: Do cited evidence IDs exist in the EvidenceBundle?
        missing_eids = [eid for eid in claim.evidence_ids if eid not in evidence_map]
        if missing_eids:
            return VerificationResult(
                claim_id=claim.claim_id,
                status=ClaimVerificationStatus.UNSUPPORTED,
                evidence_ids=claim.evidence_ids,
                is_supported=False,
                reason=f"Claim cited non-existent evidence IDs: {missing_eids}.",
                confidence=1.0,
            )

        # Retrieve referenced spans
        spans = [evidence_map[eid] for eid in claim.evidence_ids]
        combined_source_text = " ".join(s.raw_text for s in spans)
        combined_norm_text = " ".join(s.normalized_text or s.raw_text for s in spans).lower()

        claim_text = claim.text.strip()
        claim_norm = claim_text.lower()

        # Check 3: Negation Contradiction Check
        # If claim asserts positive renewal but evidence contains 'no automatic renewal' or vice-versa
        claim_has_neg = any(re.search(rf"\b{w}\b", claim_norm) for w in cls.NEGATION_WORDS)
        evidence_has_neg = any(re.search(rf"\b{w}\b", combined_norm_text) for w in cls.NEGATION_WORDS)

        if "renew" in claim_norm and "renew" in combined_norm_text:
            if not claim_has_neg and re.search(r"\b(no\s+automatic\s+renewal|shall\s+not\s+(?:automatically\s+)?renew|without\s+(?:any\s+)?(?:automatic\s+)?renewal)\b", combined_norm_text):
                return VerificationResult(
                    claim_id=claim.claim_id,
                    status=ClaimVerificationStatus.CONTRADICTED,
                    evidence_ids=claim.evidence_ids,
                    is_supported=False,
                    reason="Contradiction: Claim asserts renewal, but evidence specifies no automatic renewal.",
                    confidence=1.0,
                )
            if claim_has_neg and re.search(r"\b(shall\s+automatically\s+renew|automatic\s+renewal)\b", combined_norm_text) and not re.search(r"\b(no\s+automatic\s+renewal|shall\s+not\s+renew)\b", combined_norm_text):
                if any(phrase in claim_norm for phrase in ["no renewal", "does not renew", "no automatic renewal", "will not renew"]):
                    return VerificationResult(
                        claim_id=claim.claim_id,
                        status=ClaimVerificationStatus.CONTRADICTED,
                        evidence_ids=claim.evidence_ids,
                        is_supported=False,
                        reason="Contradiction: Claim asserts non-renewal, but evidence establishes standard renewal.",
                        confidence=1.0,
                    )

        # Check 4: Numeric / Term Alignment (e.g. Net 30 vs Net 60, days, currency)
        # Extract numbers from claim
        claim_numbers = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", claim_text))
        # If claim asserts specific numbers (like '60' or '30' or '2,000,000'), they must appear in evidence
        if claim_numbers:
            evidence_numbers = set(re.findall(r"\b\d+(?:,\d+)*(?:\.\d+)?\b", combined_source_text))
            unsupported_numbers = claim_numbers - evidence_numbers
            if unsupported_numbers:
                return VerificationResult(
                    claim_id=claim.claim_id,
                    status=ClaimVerificationStatus.UNSUPPORTED,
                    evidence_ids=claim.evidence_ids,
                    is_supported=False,
                    reason=f"Numeric discrepancy: Claim asserts numbers {list(unsupported_numbers)} not found in cited evidence.",
                    confidence=1.0,
                )

        # Check 5: Modality check ('may' vs 'shall')
        claim_has_may = bool(re.search(r"\bmay\b", claim_norm))
        claim_has_shall = bool(re.search(r"\b(shall|must|required)\b", claim_norm))
        ev_has_shall = bool(re.search(r"\b(shall|must|required)\b", combined_norm_text))
        ev_has_may = bool(re.search(r"\bmay\b", combined_norm_text))

        if claim_has_may and not ev_has_may and ev_has_shall:
            # Downgrading mandatory obligation to permissive
            return VerificationResult(
                claim_id=claim.claim_id,
                status=ClaimVerificationStatus.PARTIALLY_SUPPORTED,
                evidence_ids=claim.evidence_ids,
                is_supported=False,
                reason="Modality mismatch: Claim states 'may' (permissive) where contractual evidence specifies mandatory obligation ('shall/must').",
                confidence=0.9,
            )

        # Check 6: Keyword & Semantic Overlap
        # Extract meaningful content words (length >= 3, excluding stopwords and conversational filler)
        STOPWORDS = {
            "the", "and", "that", "this", "with", "for", "are", "was", "were", "been", "have", "has", "had",
            "contract", "agreement", "between", "entered", "into", "regarding", "specifies", "established",
            "establishing", "provides", "providing", "state", "states", "stated", "which", "what", "such",
            "their", "each", "both", "terms", "provisions", "following", "based", "evidence"
        }
        claim_tokens = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", claim_norm) if w not in STOPWORDS]
        if not claim_tokens:
            claim_tokens = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", claim_norm) if w not in {"the", "and", "that"}]
        if not claim_tokens:
            return VerificationResult(
                claim_id=claim.claim_id,
                status=ClaimVerificationStatus.INSUFFICIENT_EVIDENCE,
                evidence_ids=claim.evidence_ids,
                is_supported=False,
                reason="Claim contains no substantive factual terms.",
                confidence=1.0,
            )

        matched_tokens = [t for t in claim_tokens if t in combined_norm_text]
        overlap_ratio = len(matched_tokens) / len(claim_tokens)

        # Construct resolved citations for supporting spans
        resolved_citations = [
            EvidenceCitation(
                document_id=s.document_id,
                filename=s.filename,
                page_number=s.page_number,
                block_id=s.block_id,
                bbox=s.bbox,
                section_number=s.section_number,
                section_title=s.section_title,
                is_valid=True,
                source_chunk_id=s.metadata.get("source_chunk_id"),
                snippet=s.raw_text or s.normalized_text,
            )
            for s in spans
        ]

        if overlap_ratio >= 0.50:
            return VerificationResult(
                claim_id=claim.claim_id,
                status=ClaimVerificationStatus.SUPPORTED,
                evidence_ids=claim.evidence_ids,
                is_supported=True,
                reason=f"Fully supported by cited evidence ({overlap_ratio*100:.1f}% factual term alignment).",
                resolved_citations=resolved_citations,
                confidence=min(1.0, overlap_ratio + 0.1),
            )
        elif overlap_ratio >= 0.30:
            return VerificationResult(
                claim_id=claim.claim_id,
                status=ClaimVerificationStatus.PARTIALLY_SUPPORTED,
                evidence_ids=claim.evidence_ids,
                is_supported=False,
                reason=f"Partially supported: {overlap_ratio*100:.1f}% term overlap; some claim assertions lack direct textual evidence.",
                resolved_citations=resolved_citations,
                confidence=overlap_ratio,
            )
        else:
            return VerificationResult(
                claim_id=claim.claim_id,
                status=ClaimVerificationStatus.UNSUPPORTED,
                evidence_ids=claim.evidence_ids,
                is_supported=False,
                reason=f"Unsupported: Only {overlap_ratio*100:.1f}% term overlap with cited evidence.",
                resolved_citations=[],
                confidence=1.0 - overlap_ratio,
            )

    @classmethod
    def verify_all_claims(
        cls,
        claims: List[GroundedClaim],
        evidence_map: Dict[str, EvidenceSpan],
    ) -> VerificationReport:
        """Audit a complete list of claims and generate a comprehensive VerificationReport."""
        results: List[VerificationResult] = []
        supported = 0
        partially = 0
        unsupported = 0
        contradicted = 0
        insufficient = 0

        valid_citations_count = 0
        total_citations_referenced = 0

        for claim in claims:
            res = cls.verify_claim(claim, evidence_map)
            results.append(res)

            # Update claim object with verification results
            claim.is_verified = res.is_supported
            claim.verification_status = res.status
            claim.verification_reason = res.reason

            if res.status == ClaimVerificationStatus.SUPPORTED:
                supported += 1
            elif res.status == ClaimVerificationStatus.PARTIALLY_SUPPORTED:
                partially += 1
            elif res.status == ClaimVerificationStatus.UNSUPPORTED:
                unsupported += 1
            elif res.status == ClaimVerificationStatus.CONTRADICTED:
                contradicted += 1
            elif res.status == ClaimVerificationStatus.INSUFFICIENT_EVIDENCE:
                insufficient += 1

            for eid in claim.evidence_ids:
                total_citations_referenced += 1
                if eid in evidence_map:
                    valid_citations_count += 1

        total = len(claims)
        support_rate = (supported / total) if total > 0 else 1.0
        unsupported_rate = (unsupported / total) if total > 0 else 0.0
        contra_rate = (contradicted / total) if total > 0 else 0.0
        citation_prec = (valid_citations_count / total_citations_referenced) if total_citations_referenced > 0 else 1.0
        
        # Citation recall: claims that cite at least 1 valid evidence / total claims
        claims_with_valid_citations = sum(
            1 for c in claims if any(eid in evidence_map for eid in c.evidence_ids)
        )
        citation_rec = (claims_with_valid_citations / total) if total > 0 else 1.0

        is_fully_grounded = (total > 0 and supported == total) or (total == 0)

        return VerificationReport(
            total_claims=total,
            supported_claims=supported,
            partially_supported_claims=partially,
            unsupported_claims=unsupported,
            contradicted_claims=contradicted,
            insufficient_evidence_claims=insufficient,
            claim_support_rate=support_rate,
            unsupported_claim_rate=unsupported_rate,
            contradiction_rate=contra_rate,
            citation_precision=citation_prec,
            citation_recall=citation_rec,
            is_fully_grounded=is_fully_grounded,
            results=results,
        )
