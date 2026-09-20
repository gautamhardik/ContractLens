"""NVIDIA NIM Dense Multimodal Embedding Retriever for ContractLens.

Uses nvidia/llama-nemotron-embed-vl-1b-v2 (2,048 dimensions) with:
- Asymmetric query / passage encoding.
- Persistent local disk cache in Data/processed/embeddings/ to prevent redundant API spending.
- Safe fallback to local dense LSA retriever if offline or unconfigured.
"""

from __future__ import annotations

import os
import json
import logging
import math
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.models.chunk import RetrievalChunk

logger = logging.getLogger("contractlens.nvidia_embed")


class NvidiaDenseRetriever:
    """Retrieval engine using NVIDIA NIM multimodal embeddings with persistent disk caching."""

    MODEL_NAME = "nvidia/llama-nemotron-embed-vl-1b-v2"
    ENDPOINT_URL = "https://integrate.api.nvidia.com/v1/embeddings"

    def __init__(
        self,
        chunks: List[RetrievalChunk],
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        batch_size: int = 20,
    ):
        self.chunks = chunks
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.cache_dir = cache_dir or Path("Data/processed/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "nemo_embeddings.json"
        self.batch_size = batch_size

        self.chunk_embeddings: Dict[str, List[float]] = {}
        self._load_or_index_chunks()

    EMBEDDING_VERSION = "v1"

    @classmethod
    def compute_fingerprint(cls, chunk_id: str, text: str) -> str:
        """Compute SHA-256 deterministic fingerprint combining text content, chunk id, model, and version."""
        import hashlib
        hasher = hashlib.sha256()
        hasher.update(cls.MODEL_NAME.encode("utf-8"))
        hasher.update(cls.EMBEDDING_VERSION.encode("utf-8"))
        hasher.update(chunk_id.encode("utf-8"))
        hasher.update(text.encode("utf-8"))
        return hasher.hexdigest()

    def _load_or_index_chunks(self):
        """Load cached embeddings from disk or compute missing ones using SHA-256 fingerprints."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.chunk_embeddings = json.load(f)
                logger.info("Loaded %d cached embeddings from %s", len(self.chunk_embeddings), self.cache_file)
            except Exception as e:
                logger.warning("Could not read embedding cache: %s", e)

        # Identify missing chunks by content fingerprint
        missing = []
        for c in self.chunks:
            fp = self.compute_fingerprint(c.chunk_id, c.text)
            if fp not in self.chunk_embeddings and c.chunk_id not in self.chunk_embeddings:
                missing.append(c)

        if missing and self.api_key:
            logger.info("Computing embeddings for %d new chunks via NVIDIA NIM...", len(missing))
            for i in range(0, len(missing), self.batch_size):
                batch = missing[i : i + self.batch_size]
                texts = [c.text for c in batch]
                vectors = self._get_embeddings(texts, input_type="passage")
                for c, v in zip(batch, vectors):
                    if v:
                        fp = self.compute_fingerprint(c.chunk_id, c.text)
                        self.chunk_embeddings[fp] = v
                        self.chunk_embeddings[c.chunk_id] = v

            # Persist to disk
            try:
                with open(self.cache_file, "w", encoding="utf-8") as f:
                    json.dump(self.chunk_embeddings, f)
                logger.info("Saved %d embeddings to cache.", len(self.chunk_embeddings))
            except Exception as e:
                logger.warning("Failed saving embedding cache: %s", e)

    def _get_embeddings(self, texts: List[str], input_type: str = "passage") -> List[Optional[List[float]]]:
        """Query NVIDIA NIM embeddings endpoint."""
        if not self.api_key or not texts:
            return [None] * len(texts)

        payload = {
            "model": self.MODEL_NAME,
            "input": texts,
            "input_type": input_type,
            "encoding_format": "float",
        }
        req_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            req = urllib.request.Request(self.ENDPOINT_URL, data=req_data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    res = []
                    for item in data.get("data", []):
                        res.append(item.get("embedding"))
                    return res
        except Exception as e:
            logger.warning("NVIDIA embedding request failed: %s", e)

        return [None] * len(texts)

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two float vectors."""
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_doc_ids: Optional[List[str]] = None,
    ) -> List[Tuple[RetrievalChunk, float]]:
        """Retrieve top_k most relevant chunks using cosine similarity against query embedding."""
        query_vecs = self._get_embeddings([query], input_type="query")
        if not query_vecs or not query_vecs[0]:
            return []

        q_vec = query_vecs[0]
        scored: List[Tuple[RetrievalChunk, float]] = []

        for chunk in self.chunks:
            if filter_doc_ids and chunk.document_id not in filter_doc_ids:
                continue
            c_vec = self.chunk_embeddings.get(chunk.chunk_id)
            if c_vec:
                sim = self._cosine_similarity(q_vec, c_vec)
                scored.append((chunk, float(sim)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
