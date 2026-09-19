"""Query-Adaptive Retrieval & Selective Reranking for ContractLens (Phase 20).

Consumes Phase 19 QueryUnderstanding to form a strongly typed RetrievalQuery.
Applies intent-aware candidate generation, adaptive fusion weighting,
deterministic difficulty detection, and selective FlashRank cross-encoder reranking.

Preserves 100% of chunk provenance and strictly preserves the original user query.
"""

from enum import Enum
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field

from src.models.chunk import RetrievalChunk
from src.retrieval.lexical import BM25Retriever
from src.retrieval.dense import BaseDenseRetriever
from src.retrieval.fusion import HybridRRFRetriever
from src.retrieval.reranker import FlashRankReranker
from src.agent.understanding import (
    QueryUnderstanding,
    ContractQueryUnderstander,
    QueryIntent,
    RoleResolutionStatus,
)


# ==============================================================================
# 1. RETRIEVAL QUERY ABSTRACTION
# ==============================================================================

class RetrievalQuery(BaseModel):
    """Normalized retrieval query representation driven by Phase 19 QueryUnderstanding."""
    original_query: str
    expanded_query: str
    intent: QueryIntent
    target_document_ids: List[str] = Field(default_factory=list)
    resolved_parties: List[str] = Field(default_factory=list)
    expansion_terms: List[str] = Field(default_factory=list)
    is_amendment_or_comparison: bool = False
    understanding: Optional[QueryUnderstanding] = None

    @classmethod
    def from_understanding(
        cls,
        understanding: QueryUnderstanding,
        target_document_ids: Optional[List[str]] = None,
    ) -> "RetrievalQuery":
        """Create a RetrievalQuery strictly from a Phase 19 QueryUnderstanding object."""
        docs = list(target_document_ids or [])
        if understanding.target_document_id and understanding.target_document_id not in docs:
            docs.append(understanding.target_document_id)

        resolved_parties = []
        for rc in understanding.role_candidates:
            if rc.status == RoleResolutionStatus.RESOLVED and rc.resolved_party:
                if rc.resolved_party not in resolved_parties:
                    resolved_parties.append(rc.resolved_party)

        is_amendment_or_comparison = (
            understanding.intent in (QueryIntent.AMENDMENT, QueryIntent.COMPARISON)
            or understanding.comparison_cue is not None
        )

        return cls(
            original_query=understanding.original_query,
            expanded_query=understanding.expanded_query.expanded_query,
            intent=understanding.intent,
            target_document_ids=docs,
            resolved_parties=resolved_parties,
            expansion_terms=understanding.expanded_query.expansion_terms,
            is_amendment_or_comparison=is_amendment_or_comparison,
            understanding=understanding,
        )

    @classmethod
    def from_raw_query(
        cls,
        query: str,
        target_document_ids: Optional[List[str]] = None,
    ) -> "RetrievalQuery":
        """Analyze raw query via ContractQueryUnderstander and build RetrievalQuery."""
        u = ContractQueryUnderstander.analyze_query(query)
        return cls.from_understanding(u, target_document_ids=target_document_ids)


# ==============================================================================
# 2. DIFFICULTY DETECTOR & SIGNALS
# ==============================================================================

class RetrievalDifficulty(str, Enum):
    """Deterministic classification of candidate pool ambiguity."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class DifficultySignals(BaseModel):
    """Calculated ambiguity signals from candidate retrieval pools."""
    top_score: float
    second_score: float
    score_margin: float
    doc_competition: int  # Number of distinct documents in top candidates
    lexical_dense_agreement: float  # Jaccard overlap between top lexical and dense candidates
    is_amendment_or_comparison: bool
    difficulty: RetrievalDifficulty
    trigger_reason: str = ""


class DifficultyDetector:
    """Deterministic rule-based ambiguity detector for selective reranking.
    
    CRITICAL INVARIANT: The difficulty detector determines ONLY whether to invoke
    cross-encoder reranking. It NEVER determines query answerability.
    """

    def __init__(
        self,
        score_margin_threshold: float = 0.003,
        agreement_threshold: float = 0.20,
        doc_competition_threshold: int = 3,
    ):
        self.score_margin_threshold = score_margin_threshold
        self.agreement_threshold = agreement_threshold
        self.doc_competition_threshold = doc_competition_threshold

    def evaluate(
        self,
        retrieval_query: RetrievalQuery,
        fused_candidates: List[Tuple[RetrievalChunk, float]],
        lexical_candidates: List[Tuple[RetrievalChunk, float]],
        dense_candidates: List[Tuple[RetrievalChunk, float]],
        top_n_eval: int = 5,
    ) -> DifficultySignals:
        """Compute difficulty signals deterministically."""
        if not fused_candidates:
            return DifficultySignals(
                top_score=0.0,
                second_score=0.0,
                score_margin=0.0,
                doc_competition=0,
                lexical_dense_agreement=1.0,
                is_amendment_or_comparison=retrieval_query.is_amendment_or_comparison,
                difficulty=RetrievalDifficulty.LOW,
                trigger_reason="empty_candidates",
            )

        top_score = fused_candidates[0][1]
        second_score = fused_candidates[1][1] if len(fused_candidates) > 1 else 0.0
        score_margin = top_score - second_score

        # Distinct documents in top-N
        top_docs = {c.document_id for c, _ in fused_candidates[:top_n_eval]}
        doc_competition = len(top_docs)

        # Lexical vs Dense Jaccard Agreement in top-N
        lex_cids = {c.chunk_id for c, _ in lexical_candidates[:top_n_eval]}
        dense_cids = {c.chunk_id for c, _ in dense_candidates[:top_n_eval]}
        if lex_cids or dense_cids:
            intersection = len(lex_cids.intersection(dense_cids))
            union = len(lex_cids.union(dense_cids))
            agreement = (intersection / union) if union > 0 else 0.0
        else:
            agreement = 1.0

        # Classification rules
        triggers = []
        is_high = False

        if retrieval_query.is_amendment_or_comparison:
            is_high = True
            triggers.append("amendment_or_comparison")

        if len(retrieval_query.target_document_ids) <= 1 and doc_competition >= self.doc_competition_threshold:
            is_high = True
            triggers.append(f"doc_competition={doc_competition}")

        if len(fused_candidates) > 1 and score_margin < self.score_margin_threshold:
            is_high = True
            triggers.append(f"narrow_margin={score_margin:.5f}")

        if agreement < self.agreement_threshold:
            is_high = True
            triggers.append(f"low_model_agreement={agreement:.2f}")

        difficulty = RetrievalDifficulty.HIGH if is_high else RetrievalDifficulty.LOW
        trigger_reason = "; ".join(triggers) if triggers else "clear_margin_and_agreement"

        return DifficultySignals(
            top_score=top_score,
            second_score=second_score,
            score_margin=score_margin,
            doc_competition=doc_competition,
            lexical_dense_agreement=agreement,
            is_amendment_or_comparison=retrieval_query.is_amendment_or_comparison,
            difficulty=difficulty,
            trigger_reason=trigger_reason,
        )


# ==============================================================================
# 3. QUERY-ADAPTIVE RETRIEVER
# ==============================================================================

class AdaptiveRetriever:
    """Contract-aware adaptive retriever with selective FlashRank reranking.
    
    Supports:
    1. Static Hybrid RRF (Control)
    2. Expanded Query Hybrid RRF
    3. Intent-Adaptive Weighting
    4. Selective FlashRank Cross-Encoder Reranking
    """

    DEFAULT_INTENT_WEIGHTS: Dict[QueryIntent, Tuple[float, float]] = {
        QueryIntent.PAYMENT: (0.7, 0.3),          # Lexical heavy for exact formulas/terms
        QueryIntent.CONTRACT_DETAILS: (0.7, 0.3), # Lexical heavy for governing law / metadata
        QueryIntent.OBLIGATION: (0.5, 0.5),       # Balanced for commitments & actions
        QueryIntent.TIMELINE: (0.5, 0.5),         # Balanced for operational milestones
        QueryIntent.AMENDMENT: (0.6, 0.4),        # Moderate lexical for section refs
        QueryIntent.COMPARISON: (0.5, 0.5),       # Balanced
        QueryIntent.CROSS_CONTRACT: (0.5, 0.5),   # Balanced
        QueryIntent.INFORMATION: (0.5, 0.5),      # Default balanced
        QueryIntent.UNANSWERABLE: (0.5, 0.5),
        QueryIntent.UNKNOWN: (0.5, 0.5),
    }

    def __init__(
        self,
        lexical_retriever: BM25Retriever,
        dense_retriever: BaseDenseRetriever,
        reranker: Optional[FlashRankReranker] = None,
        rrf_k: int = 60,
        enable_query_expansion: bool = True,
        enable_adaptive_weights: bool = True,
        enable_selective_reranking: bool = True,
        always_rerank: bool = False,
        difficulty_detector: Optional[DifficultyDetector] = None,
        intent_weights: Optional[Dict[QueryIntent, Tuple[float, float]]] = None,
    ):
        self.lexical_retriever = lexical_retriever
        self.dense_retriever = dense_retriever
        self.reranker = reranker
        self.rrf_k = rrf_k
        self.enable_query_expansion = enable_query_expansion
        self.enable_adaptive_weights = enable_adaptive_weights
        self.enable_selective_reranking = enable_selective_reranking
        self.always_rerank = always_rerank
        self.detector = difficulty_detector or DifficultyDetector()
        self.intent_weights = intent_weights or dict(self.DEFAULT_INTENT_WEIGHTS)
        self.last_difficulty_signals: Optional[DifficultySignals] = None
        self.last_rerank_applied: bool = False

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filter_doc_ids: Optional[List[str]] = None,
        candidate_pool: int = 50,
        retrieval_query: Optional[RetrievalQuery] = None,
    ) -> List[Tuple[RetrievalChunk, float]]:
        """Execute adaptive retrieval workflow and return (chunk, score) tuples."""
        # 1. Build or normalize RetrievalQuery
        rq = retrieval_query or RetrievalQuery.from_raw_query(query, target_document_ids=filter_doc_ids)
        effective_filters = rq.target_document_ids or filter_doc_ids

        # 2. Select search query (expansion vs original)
        # Note: original_query remains immutable for provenance and verification
        search_query = rq.expanded_query if (self.enable_query_expansion and rq.expanded_query) else rq.original_query

        # 3. Retrieve Candidate Pools from Lexical and Dense
        lexical_results = self.lexical_retriever.retrieve(
            search_query, top_k=candidate_pool, filter_doc_ids=effective_filters
        )
        dense_results = self.dense_retriever.retrieve(
            search_query, top_k=candidate_pool, filter_doc_ids=effective_filters
        )

        # 4. Adaptive RRF Fusion
        w_lex, w_dense = (1.0, 1.0)
        if self.enable_adaptive_weights:
            w_pair = self.intent_weights.get(rq.intent, (0.5, 0.5))
            # Normalize weights so sum = 2.0 (matching baseline 1.0 + 1.0)
            w_lex = w_pair[0] * 2.0
            w_dense = w_pair[1] * 2.0

        chunk_map: Dict[str, RetrievalChunk] = {}
        rrf_scores: Dict[str, float] = {}

        for rank, (chunk, score) in enumerate(lexical_results, start=1):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + w_lex * (1.0 / (self.rrf_k + rank))

        for rank, (chunk, score) in enumerate(dense_results, start=1):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + w_dense * (1.0 / (self.rrf_k + rank))

        ranked_items = sorted(
            rrf_scores.items(),
            key=lambda item: (-item[1], item[0])
        )

        fused_candidates = [(chunk_map[cid], score) for cid, score in ranked_items]

        # 5. Difficulty Detection & Reranking Decision
        should_rerank = False
        signals = None
        if self.reranker is not None:
            if self.always_rerank:
                should_rerank = True
            elif self.enable_selective_reranking:
                signals = self.detector.evaluate(
                    retrieval_query=rq,
                    fused_candidates=fused_candidates,
                    lexical_candidates=lexical_results,
                    dense_candidates=dense_results,
                    top_n_eval=5,
                )
                should_rerank = (signals.difficulty == RetrievalDifficulty.HIGH)

        self.last_difficulty_signals = signals
        self.last_rerank_applied = should_rerank

        # 6. Apply Reranking or Truncate
        if should_rerank and self.reranker is not None and fused_candidates:
            # FlashRank reranks candidates against the user's original query
            # strictly preserving chunk identity and provenance
            rerank_pool = fused_candidates[:top_k * 2] if len(fused_candidates) >= top_k * 2 else fused_candidates
            reranked = self.reranker.rerank(
                query=rq.original_query,
                candidates=rerank_pool,
                top_k=top_k,
            )
            return reranked

        return fused_candidates[:top_k]
