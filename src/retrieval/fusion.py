"""Reciprocal Rank Fusion (RRF) Hybrid Retrieval for ContractLens (Phase 13).

Combines rankings from BM25 (lexical) and Dense (semantic) retrievers using
the standard Reciprocal Rank Fusion formula:
    RRF_score(d) = \sum_{m \in Models} \frac{1}{k + rank_m(d)}

Preserves individual retrieval rankings, composite scores, and 100% chunk provenance.
"""

from typing import List, Dict, Any, Optional, Tuple

from src.models.chunk import RetrievalChunk
from src.retrieval.lexical import BM25Retriever
from src.retrieval.dense import BaseDenseRetriever


class HybridRRFRetriever:
    """Hybrid retriever combining Lexical (BM25) and Dense (Semantic) rankings via RRF."""

    def __init__(
        self,
        lexical_retriever: BM25Retriever,
        dense_retriever: BaseDenseRetriever,
        rrf_k: int = 60,
    ):
        self.lexical_retriever = lexical_retriever
        self.dense_retriever = dense_retriever
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filter_doc_ids: Optional[List[str]] = None,
        candidate_pool: int = 50,
    ) -> List[Tuple[RetrievalChunk, float]]:
        """Perform hybrid retrieval via RRF.

        Args:
            query: Natural language question or phrase.
            top_k: Number of final fused chunks to return.
            filter_doc_ids: Optional document filters.
            candidate_pool: Number of candidate chunks to fetch from each retriever.

        Returns:
            List of (RetrievalChunk, rrf_score) tuples sorted descending.
        """
        # Step 1: Retrieve candidate pools from both retrievers
        lexical_results = self.lexical_retriever.retrieve(
            query, top_k=candidate_pool, filter_doc_ids=filter_doc_ids
        )
        dense_results = self.dense_retriever.retrieve(
            query, top_k=candidate_pool, filter_doc_ids=filter_doc_ids
        )

        # Step 2: Calculate RRF scores
        # rrf_score = sum(1.0 / (k + rank))
        chunk_map: Dict[str, RetrievalChunk] = {}
        rrf_scores: Dict[str, float] = {}

        # Process Lexical rankings (1-indexed rank)
        for rank, (chunk, score) in enumerate(lexical_results, start=1):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        # Process Dense rankings (1-indexed rank)
        for rank, (chunk, score) in enumerate(dense_results, start=1):
            cid = chunk.chunk_id
            chunk_map[cid] = chunk
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank))

        # Step 3: Sort by RRF score descending; stable tie-break by chunk_id
        ranked_items = sorted(
            rrf_scores.items(),
            key=lambda item: (-item[1], item[0])
        )

        # Step 4: Assemble top_k output
        final_results: List[Tuple[RetrievalChunk, float]] = []
        for cid, score in ranked_items[:top_k]:
            final_results.append((chunk_map[cid], score))

        return final_results
