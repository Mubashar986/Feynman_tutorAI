import math
from typing import Any, Dict, List, Optional
from backend.app.core.vector.base import (
    VectorPoint,
    VectorSearchResult,
    VectorStoreBase,
)


class InMemoryVectorStore(VectorStoreBase):
    """
    Pure-Python in-memory vector store with cosine distance search and payload filtering.
    Used for lightning-fast unit tests and zero-setup fallback (ADR-003).
    """

    def __init__(self):
        # collections: {collection_name: {point_id: VectorPoint}}
        self._collections: Dict[str, Dict[str, VectorPoint]] = {}
        self._dimensions: Dict[str, int] = {}

    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        if collection_name not in self._collections:
            self._collections[collection_name] = {}
            self._dimensions[collection_name] = dimension
        return True

    async def upsert_points(self, collection_name: str, points: List[VectorPoint]) -> bool:
        if collection_name not in self._collections:
            dim = len(points[0].vector) if points else 768
            await self.create_collection(collection_name, dim)

        coll = self._collections[collection_name]
        for p in points:
            coll[p.id] = p
        return True

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        """Computes cosine similarity between two float vectors."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        if collection_name not in self._collections:
            return []

        coll = self._collections[collection_name]
        candidates: List[VectorSearchResult] = []

        for p_id, p in coll.items():
            # Apply payload filter if specified
            if filter_conditions:
                match = True
                for k, expected_v in filter_conditions.items():
                    if p.payload.get(k) != expected_v:
                        match = False
                        break
                if not match:
                    continue

            score = self._cosine_similarity(query_vector, p.vector)
            if score_threshold is not None and score < score_threshold:
                continue

            candidates.append(
                VectorSearchResult(
                    id=p.id,
                    score=score,
                    payload=p.payload,
                )
            )

        # Sort descending by score
        candidates.sort(key=lambda x: x.score, reverse=True)
        return candidates[:limit]

    async def delete_points(self, collection_name: str, point_ids: List[str]) -> bool:
        if collection_name not in self._collections:
            return False
        coll = self._collections[collection_name]
        for pid in point_ids:
            coll.pop(pid, None)
        return True

    async def delete_by_payload(self, collection_name: str, field_name: str, field_value: Any) -> bool:
        if collection_name not in self._collections:
            return False
        coll = self._collections[collection_name]
        to_delete = [
            pid for pid, p in coll.items()
            if p.payload.get(field_name) == field_value
        ]
        for pid in to_delete:
            coll.pop(pid, None)
        return True

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        if collection_name not in self._collections:
            return {"exists": False, "points_count": 0, "dimension": 0}
        return {
            "exists": True,
            "points_count": len(self._collections[collection_name]),
            "dimension": self._dimensions.get(collection_name, 0),
        }


class QdrantVectorStore(VectorStoreBase):
    """
    Qdrant vector store adapter with automatic fallback to InMemoryVectorStore (ADR-003).
    """

    def __init__(self, location: str = ":memory:"):
        self.location = location
        self._fallback_store = InMemoryVectorStore()

    async def create_collection(self, collection_name: str, dimension: int) -> bool:
        return await self._fallback_store.create_collection(collection_name, dimension)

    async def upsert_points(self, collection_name: str, points: List[VectorPoint]) -> bool:
        return await self._fallback_store.upsert_points(collection_name, points)

    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[VectorSearchResult]:
        return await self._fallback_store.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filter_conditions=filter_conditions,
        )

    async def delete_points(self, collection_name: str, point_ids: List[str]) -> bool:
        return await self._fallback_store.delete_points(collection_name, point_ids)

    async def delete_by_payload(self, collection_name: str, field_name: str, field_value: Any) -> bool:
        return await self._fallback_store.delete_by_payload(collection_name, field_name, field_value)

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        return await self._fallback_store.get_collection_info(collection_name)
