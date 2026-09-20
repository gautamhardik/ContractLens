"""In-Memory Repository Implementations for ContractLens.

Fulfills DocumentRepository, IntelligenceRepository, and CacheRepository interfaces
using high-performance in-memory and disk-backed storage structures.
"""

from typing import Dict, List, Optional, Any
from src.repositories.interfaces import (
    DocumentRepository,
    IntelligenceRepository,
    CacheRepository,
)
from src.models.canonical import CanonicalDocument
from src.models.intelligence import ContractIntelligence
from src.models.obligation import ContractObligation, LifecycleEvent


class InMemoryDocumentRepository(DocumentRepository):
    """In-memory implementation of DocumentRepository."""

    def __init__(self):
        self._docs: Dict[str, CanonicalDocument] = {}

    def get_document(self, document_id: str) -> Optional[CanonicalDocument]:
        return self._docs.get(document_id)

    def list_documents(self) -> List[CanonicalDocument]:
        return list(self._docs.values())

    def save_document(self, document: CanonicalDocument) -> None:
        self._docs[document.document_id] = document

    def delete_document(self, document_id: str) -> bool:
        if document_id in self._docs:
            del self._docs[document_id]
            return True
        return False

    def clear(self) -> None:
        self._docs.clear()

    def __len__(self) -> int:
        return len(self._docs)


class InMemoryIntelligenceRepository(IntelligenceRepository):
    """In-memory implementation of IntelligenceRepository."""

    def __init__(self):
        self._intelligence: Dict[str, ContractIntelligence] = {}
        self._obligations: List[ContractObligation] = []
        self._events: List[LifecycleEvent] = []

    def get_intelligence(self, document_id: str) -> Optional[ContractIntelligence]:
        return self._intelligence.get(document_id)

    def save_intelligence(self, document_id: str, intelligence: ContractIntelligence) -> None:
        self._intelligence[document_id] = intelligence

    def list_all_intelligence(self) -> Dict[str, ContractIntelligence]:
        return dict(self._intelligence)

    def get_obligations(self, document_id: Optional[str] = None) -> List[ContractObligation]:
        if document_id:
            return [ob for ob in self._obligations if ob.evidence.document_id == document_id]
        return list(self._obligations)

    def add_obligations(self, obligations: List[ContractObligation]) -> None:
        self._obligations.extend(obligations)

    def get_lifecycle_events(self, document_id: Optional[str] = None) -> List[LifecycleEvent]:
        if document_id:
            return [ev for ev in self._events if ev.evidence.document_id == document_id]
        return list(self._events)

    def add_lifecycle_events(self, events: List[LifecycleEvent]) -> None:
        self._events.extend(events)

    def clear(self) -> None:
        self._intelligence.clear()
        self._obligations.clear()
        self._events.clear()


class InMemoryCacheRepository(CacheRepository):
    """In-memory implementation of CacheRepository."""

    def __init__(self):
        self._portfolio_bytes: Optional[bytes] = None
        self._risks_bytes: Optional[bytes] = None
        self._summaries_bytes: Optional[bytes] = None
        self._query_cache: Dict[str, Dict[str, Any]] = {}

    def get_precomputed_portfolio(self) -> Optional[bytes]:
        return self._portfolio_bytes

    def set_precomputed_portfolio(self, data: bytes) -> None:
        self._portfolio_bytes = data

    def get_precomputed_risks(self) -> Optional[bytes]:
        return self._risks_bytes

    def set_precomputed_risks(self, data: bytes) -> None:
        self._risks_bytes = data

    def get_precomputed_summaries(self) -> Optional[bytes]:
        return self._summaries_bytes

    def set_precomputed_summaries(self, data: bytes) -> None:
        self._summaries_bytes = data

    def get_cached_query(self, cache_key: str) -> Optional[Dict[str, Any]]:
        return self._query_cache.get(cache_key)

    def set_cached_query(self, cache_key: str, response: Dict[str, Any]) -> None:
        self._query_cache[cache_key] = response

    def clear_query_cache(self) -> None:
        self._query_cache.clear()
