from backend.app.core.storage.base import StorageProvider
from backend.app.core.storage.local import LocalStorageProvider

_default_storage_provider: StorageProvider = LocalStorageProvider()


def get_storage_provider() -> StorageProvider:
    """Returns the singleton storage provider instance."""
    return _default_storage_provider


__all__ = [
    "StorageProvider",
    "LocalStorageProvider",
    "get_storage_provider",
]
