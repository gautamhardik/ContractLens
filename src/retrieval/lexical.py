"""BM25 Lexical Retrieval for ContractLens (Phase 13).

Provides deterministic lexical retrieval scoring using Okapi BM25 algorithm
with full preservation of chunk provenance, configurable top-k, and metadata filtering.
"""

import math
import re
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

from src.models.chunk import RetrievalChunk


def tokenize(text: str) -> List[str]:
    """Clean, lowercase, and tokenize text into words."""
    if not text:
        return []
    tokens = re.findall(r'\b[a-zA-Z0-9_\-\.\$]+\b', text.lower())
    return tokens


class BM25Retriever:
    """Deterministic BM25 Okapi retriever for RetrievalChunks."""

    def __init__(
        self,
        chunks: List[RetrievalChunk],
        k1: float = 1.5,
        b: float = 0.75,
        epsilon: float = 0.25,
    ):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.epsilon = epsilon
        self.corpus_size = len(chunks)
        
        # Tokenize corpus and calculate statistics
        self.doc_tokens: List[List[str]] = []
        self.doc_lens: List[int] = []
        self.doc_freqs: Dict[str, int] = Counter()
        
        total_len = 0
        for chunk in self.chunks:
            tokens = tokenize(chunk.text)
            self.doc_tokens.append(tokens)
            l = len(tokens)
            self.doc_lens.append(l)
            total_len += l
            
            # Count document frequencies
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1
                
        self.avgdl = (total_len / self.corpus_size) if self.corpus_size > 0 else 1.0
        
        # Precompute IDF
        self.idf: Dict[str, float] = {}
        negative_idfs = []
        for token, freq in self.doc_freqs.items():
            # Standard Lucene/BM25 IDF: log(1 + (N - n + 0.5) / (n + 0.5))
            idf_val = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))
            self.idf[token] = idf_val
            if idf_val < 0:
                negative_idfs.append(token)
                
        # Handle negative idf if any
        if negative_idfs:
            avg_idf = sum(v for v in self.idf.values() if v > 0) / (len(self.idf) - len(negative_idfs) or 1)
            eps_idf = self.epsilon * avg_idf
            for token in negative_idfs:
                self.idf[token] = eps_idf

    def retrieve(
        self,
        query: str,
        top_k: int = 10,
        filter_doc_ids: Optional[List[str]] = None,
    ) -> List[Tuple[RetrievalChunk, float]]:
        """Retrieve top_k chunks matching query using BM25 scoring.
        
        Returns:
            List of (RetrievalChunk, bm25_score) tuples sorted descending by score.
        """
        if not self.chunks or not query or not query.strip():
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores: List[Tuple[int, float]] = []
        filter_set = set(filter_doc_ids) if filter_doc_ids else None

        for idx, (chunk, tokens, doc_len) in enumerate(zip(self.chunks, self.doc_tokens, self.doc_lens)):
            if filter_set and chunk.document_id not in filter_set:
                continue

            term_counts = Counter(tokens)
            score = 0.0
            for q_term in query_tokens:
                if q_term in term_counts:
                    tf = term_counts[q_term]
                    idf = self.idf.get(q_term, 0.0)
                    denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
                    score += idf * ((tf * (self.k1 + 1.0)) / denom)

            # Boost if section title or number appears in query
            if chunk.provenance.section_title:
                title_tokens = set(tokenize(chunk.provenance.section_title))
                matching_title = sum(1 for qt in query_tokens if qt in title_tokens)
                if matching_title > 0:
                    score += 0.5 * matching_title

            if score > 0.0:
                scores.append((idx, score))

        # Sort descending by score; stable tie-break by chunk_id
        scores.sort(key=lambda item: (-item[1], self.chunks[item[0]].chunk_id))

        results: List[Tuple[RetrievalChunk, float]] = []
        for idx, score in scores[:top_k]:
            results.append((self.chunks[idx], score))

        return results
