from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class VectorPoint:
    """A high-dimensional vector point with metadata payload."""
    id: str
    vector: List[float]
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VectorSearchResult:
    """Result of a semantic vector similarity search."""
    id: str
    score: float
    payload: Dict[str, Any] = field(default_factory=dict)


class VectorStoreBase(ABC):
    """
    Abstract Base Class defining the vector store adapter contract (ADR-003).
    Decouples application logic from specific vector database engines (Qdrant, pgvector, in-memory).
    """

    @abstractmethod
    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        """Creates a vector collection with the specified embedding dimension if it does not exist."""
        pass

    @abstractmethod
    async def upsert_points(self, collection_name: str, points: List[VectorPoint]) -> bool:
        """Inserts or updates vector points in the collection."""
        pass

    @abstractmethod
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        """Performs approximate nearest neighbor search with optional payload filtering."""
        pass

    @abstractmethod
    async def delete_points(self, collection_name: str, point_ids: List[str]) -> bool:
        """Deletes specific vector points by ID."""
        pass

    @abstractmethod
    async def delete_by_payload(self, collection_name: str, field_name: str, field_value: Any) -> bool:
        """Deletes all vector points matching a payload field condition."""
        pass

    @abstractmethod
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Returns collection metrics (points count, vector dimension)."""
        pass
