from backend.app.core.vector.base import (
    VectorPoint,
    VectorSearchResult,
    VectorStoreBase,
)
from backend.app.core.vector.qdrant import (
    InMemoryVectorStore,
    QdrantVectorStore,
)

_default_vector_store: VectorStoreBase = QdrantVectorStore(location=":memory:")


def get_vector_store() -> VectorStoreBase:
    """Returns the singleton vector store instance."""
    return _default_vector_store


__all__ = [
    "VectorPoint",
    "VectorSearchResult",
    "VectorStoreBase",
    "InMemoryVectorStore",
    "QdrantVectorStore",
    "get_vector_store",
]
