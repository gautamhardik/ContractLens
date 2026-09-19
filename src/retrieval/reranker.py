"""Cross-Encoder Reranking Interface for ContractLens (Phase 14).

Provides a modular reranker interface that re-ranks retrieved Top-K candidate chunks
without fetching new documents or modifying chunk provenance.
Supports:
1. FlashRank (ultra-lightweight ONNX-based cross-encoder, e.g. ms-marco-TinyBERT-L-2-v2, ~3.3MB)
2. Configurable candidate pool (candidate_k) and return size (top_k).
3. 100% Provenance and score preservation.
"""

from abc import ABC, abstractmethod
import time
from typing import List, Dict, Any, Optional, Tuple

from src.models.chunk import RetrievalChunk


class BaseReranker(ABC):
    """Abstract base class for all ContractLens rerankers."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[Tuple[RetrievalChunk, float]],
        top_k: int = 5,
    ) -> List[Tuple[RetrievalChunk, float]]:
        """Re-rank candidate (chunk, initial_score) tuples by query relevance."""
        pass


class FlashRankReranker(BaseReranker):
    """Ultra-lightweight ONNX-based cross-encoder reranker via FlashRank."""

    def __init__(
        self,
        model_name: str = "ms-marco-TinyBERT-L-2-v2",
        cache_dir: str = "experiments/reranking/.cache",
    ):
        from flashrank import Ranker
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.ranker = Ranker(model_name=model_name, cache_dir=cache_dir)

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[RetrievalChunk, float]],
        top_k: int = 5,
    ) -> List[Tuple[RetrievalChunk, float]]:
        from flashrank import RerankRequest

        if not candidates or not query or not query.strip():
            return candidates[:top_k]

        # Prepare passages for FlashRank while maintaining chunk lookup by index/id
        chunk_map: Dict[str, Tuple[RetrievalChunk, float]] = {}
        passages = []
        for rank_idx, (chunk, orig_score) in enumerate(candidates):
            cid = chunk.chunk_id
            chunk_map[cid] = (chunk, orig_score)
            passages.append({
                "id": cid,
                "text": chunk.text,
                "meta": {"orig_score": orig_score, "rank_idx": rank_idx}
            })

        rerank_request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(rerank_request)

        # Sort descending by cross-encoder score; tie-break by initial rank
        ranked_candidates: List[Tuple[RetrievalChunk, float]] = []
        for item in results:
            cid = item["id"]
            new_score = float(item["score"])
            chunk, orig_score = chunk_map[cid]
            ranked_candidates.append((chunk, new_score))

        return ranked_candidates[:top_k]
