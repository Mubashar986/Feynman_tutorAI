from abc import ABC, abstractmethod
from typing import Optional


class StorageProvider(ABC):
    """
    Abstract Base Class defining the pluggable object storage contract (ADR-009).
    Supports local filesystem sandboxing for zero-setup dev and S3/MinIO for production.
    """

    @abstractmethod
    async def save_file(self, file_bytes: bytes, filename: str, content_type: Optional[str] = None) -> str:
        """
        Persists raw file bytes and returns the stored file path or URI.
        """
        pass

    @abstractmethod
    async def get_file_bytes(self, storage_path: str) -> bytes:
        """
        Retrieves raw file bytes from the given storage path.
        """
        pass

    @abstractmethod
    async def delete_file(self, storage_path: str) -> bool:
        """
        Deletes the file from storage if it exists.
        """
        pass

    @abstractmethod
    def get_file_url(self, storage_path: str) -> str:
        """
        Returns a relative or absolute URL/path to access the stored file.
        """
        pass
