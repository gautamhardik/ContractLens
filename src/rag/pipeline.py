"""End-to-End Grounded RAG Pipeline for ContractLens (Phase 16).

Integrates:
Question
  ↓
Hybrid RRF Retrieval (k=60)
  ↓
Evidence Layer (Phase 15 EvidenceResolver)
  ↓
Verified EvidenceBundle
  ↓
GroundedAnswerGenerator (Phase 16)
  ↓
ClaimVerifier (Phase 16)
  ↓
Audited GroundedAnswer with Verified Citations
"""

import time
from typing import Optional, List, Dict, Any

from src.retrieval.fusion import HybridRRFRetriever
from src.evidence.resolver import EvidenceResolver
from src.evidence.models import EvidenceBundle, EvidenceCitation
from src.rag.models import (
    GroundedAnswer,
    RAGResponse,
    ClaimVerificationStatus,
    VerificationReport,
)
from src.rag.generator import GroundedAnswerGenerator, BaseLLMProvider
from src.rag.verifier import ClaimVerifier


class GroundedRAGPipeline:
    """Full operational pipeline executing Grounded RAG with strict claim verification."""

    def __init__(
        self,
        retriever: HybridRRFRetriever,
        resolver: EvidenceResolver,
        llm_provider: BaseLLMProvider,
        top_k_chunks: int = 5,
    ):
        self.retriever = retriever
        self.resolver = resolver
        self.generator = GroundedAnswerGenerator(llm_provider)
        self.top_k_chunks = top_k_chunks

    def answer_question(
        self,
        query: str,
        filter_doc_ids: Optional[List[str]] = None,
    ) -> RAGResponse:
        """Execute the end-to-end grounded query answering workflow."""
        start_pipeline = time.perf_counter()

        # Step 1: Hybrid RRF Retrieval
        t_ret_start = time.perf_counter()
        candidates = self.retriever.retrieve(
            query=query,
            top_k=self.top_k_chunks,
            filter_doc_ids=filter_doc_ids,
        )
        ret_latency = (time.perf_counter() - t_ret_start) * 1000.0
        retrieved_chunks = [c for c, _ in candidates]

        # Step 2: Evidence Layer Resolution & Provenance Validation
        bundle: EvidenceBundle = self.resolver.create_evidence_bundle(
            query=query,
            retrieved_chunks=retrieved_chunks,
        )
        res_latency = bundle.resolution_latency_ms

        # Step 3: Grounded Answer Synthesis
        raw_answer, proposed_claims, evidence_map, gen_latency = self.generator.generate_candidate_answer(
            query=query,
            bundle=bundle,
        )

        # Step 4: Independent Claim Verification
        t_ver_start = time.perf_counter()
        verification_report: VerificationReport = ClaimVerifier.verify_all_claims(
            claims=proposed_claims,
            evidence_map=evidence_map,
        )
        ver_latency = (time.perf_counter() - t_ver_start) * 1000.0

        # Step 5: Construct Final Verified Citations
        # Only attach citations from claims that are SUPPORTED or PARTIALLY_SUPPORTED
        active_citations: List[EvidenceCitation] = []
        seen_cit_keys = set()
        for res in verification_report.results:
            if res.is_supported or res.status == ClaimVerificationStatus.PARTIALLY_SUPPORTED:
                for cit in res.resolved_citations:
                    key = (cit.document_id, cit.page_number, cit.block_id)
                    if key not in seen_cit_keys:
                        active_citations.append(cit)
                        seen_cit_keys.add(key)

        # Overall grounding status
        has_refusal = (
            "does not establish" in raw_answer.lower()
            or "insufficient evidence" in raw_answer.lower()
            or "no relevant contractual evidence" in raw_answer.lower()
        )
        is_insufficient = (
            has_refusal
            or verification_report.insufficient_evidence_claims > 0
            or (len(proposed_claims) == 0 and (len(raw_answer.strip()) < 30 or "not establish" in raw_answer.lower()))
        )

        if is_insufficient:
            overall_status = ClaimVerificationStatus.INSUFFICIENT_EVIDENCE
        elif verification_report.contradicted_claims > 0:
            overall_status = ClaimVerificationStatus.CONTRADICTED
        elif verification_report.unsupported_claims > 0:
            overall_status = ClaimVerificationStatus.UNSUPPORTED
        elif verification_report.partially_supported_claims > 0:
            overall_status = ClaimVerificationStatus.PARTIALLY_SUPPORTED
        else:
            overall_status = ClaimVerificationStatus.SUPPORTED

        grounded_answer = GroundedAnswer(
            query=query,
            answer_text=raw_answer,
            claims=proposed_claims,
            citations=active_citations,
            verification_report=verification_report,
            is_insufficient_evidence=is_insufficient,
            grounding_status=overall_status,
        )

        total_latency = (time.perf_counter() - start_pipeline) * 1000.0

        return RAGResponse(
            query=query,
            answer=grounded_answer,
            evidence_bundle=bundle,
            retrieval_latency_ms=ret_latency,
            evidence_latency_ms=res_latency,
            generation_latency_ms=gen_latency,
            verification_latency_ms=ver_latency,
            total_latency_ms=total_latency,
            metadata={
                "total_claims": verification_report.total_claims,
                "supported_claims": verification_report.supported_claims,
                "citations_count": len(active_citations),
                "is_fully_grounded": verification_report.is_fully_grounded,
            },
        )
