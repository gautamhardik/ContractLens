"""Repository Interfaces for ContractLens (Gap 1).

Defines clean abstraction boundaries between domain logic/agent reasoning and underlying
storage implementations (in-memory, disk-backed, or database).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from src.models.canonical import CanonicalDocument
from src.models.intelligence import ContractIntelligence
from src.models.obligation import ContractObligation, LifecycleEvent


class DocumentRepository(ABC):
    """Abstract interface for canonical document storage and retrieval."""

    @abstractmethod
    def get_document(self, document_id: str) -> Optional[CanonicalDocument]:
        """Retrieve a canonical document by document ID."""
        pass

    @abstractmethod
    def list_documents(self) -> List[CanonicalDocument]:
        """List all canonical documents."""
        pass

    @abstractmethod
    def save_document(self, document: CanonicalDocument) -> None:
        """Persist or register a new canonical document."""
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """Remove a document by ID."""
        pass


class IntelligenceRepository(ABC):
    """Abstract interface for contract intelligence, obligations, and lifecycle events."""

    @abstractmethod
    def get_intelligence(self, document_id: str) -> Optional[ContractIntelligence]:
        """Retrieve intelligence model for a given contract."""
        pass

    @abstractmethod
    def save_intelligence(self, document_id: str, intelligence: ContractIntelligence) -> None:
        """Save extracted intelligence for a document."""
        pass

    @abstractmethod
    def list_all_intelligence(self) -> Dict[str, ContractIntelligence]:
        """Return mapping of document_id to ContractIntelligence."""
        pass

    @abstractmethod
    def get_obligations(self, document_id: Optional[str] = None) -> List[ContractObligation]:
        """Retrieve obligations, optionally filtered by document."""
        pass

    @abstractmethod
    def add_obligations(self, obligations: List[ContractObligation]) -> None:
        """Append extracted obligations."""
        pass

    @abstractmethod
    def get_lifecycle_events(self, document_id: Optional[str] = None) -> List[LifecycleEvent]:
        """Retrieve lifecycle timeline events, optionally filtered by document."""
        pass

    @abstractmethod
    def add_lifecycle_events(self, events: List[LifecycleEvent]) -> None:
        """Append lifecycle milestones."""
        pass


class CacheRepository(ABC):
    """Abstract interface for serialized response caches and query result caches."""

    @abstractmethod
    def get_precomputed_portfolio(self) -> Optional[bytes]:
        pass

    @abstractmethod
    def set_precomputed_portfolio(self, data: bytes) -> None:
        pass

    @abstractmethod
    def get_precomputed_risks(self) -> Optional[bytes]:
        pass

    @abstractmethod
    def set_precomputed_risks(self, data: bytes) -> None:
        pass

    @abstractmethod
    def get_precomputed_summaries(self) -> Optional[bytes]:
        pass

    @abstractmethod
    def set_precomputed_summaries(self, data: bytes) -> None:
        pass

    @abstractmethod
    def get_cached_query(self, cache_key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def set_cached_query(self, cache_key: str, response: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def clear_query_cache(self) -> None:
        pass
