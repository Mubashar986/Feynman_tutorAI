from abc import ABC, abstractmethod
import hashlib
import math
import random
from typing import List


class EmbeddingProviderBase(ABC):
    """
    Abstract Base Class for text embedding providers (ADR-007).
    """

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Returns the embedding vector dimension."""
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generates a dense vector embedding for a single text."""
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generates dense vector embeddings for a batch of texts."""
        pass


class MockDeterministicEmbeddingProvider(EmbeddingProviderBase):
    """
    Deterministic, unit-normalized mock embedding generator (ADR-007).
    Produces consistent 768-dimensional float vectors based on SHA-256 seed hashing.
    Used for 100% offline, zero-network, reproducible testing.
    """

    def __init__(self, dimension: int = 768):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def _generate_deterministic_vector(self, text: str) -> List[float]:
        # Compute SHA-256 of text to use as random seed
        seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        seed_int = int.from_bytes(seed_bytes[:8], byteorder="big")

        rng = random.Random(seed_int)
        raw_vector = [rng.gauss(0.0, 1.0) for _ in range(self._dimension)]

        # Unit-normalize: ||v|| = 1.0
        norm = math.sqrt(sum(x * x for x in raw_vector))
        if norm == 0.0:
            return [1.0 / math.sqrt(self._dimension)] * self._dimension

        return [x / norm for x in raw_vector]

    async def embed_text(self, text: str) -> List[float]:
        return self._generate_deterministic_vector(text)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_deterministic_vector(t) for t in texts]


_default_embedder: EmbeddingProviderBase = MockDeterministicEmbeddingProvider()


def get_embedding_provider() -> EmbeddingProviderBase:
    """Returns the singleton embedding provider instance."""
    return _default_embedder
