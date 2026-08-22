import asyncio
import hashlib
import os
from pathlib import Path
from typing import Optional

from backend.app.core.storage.base import StorageProvider


class LocalStorageProvider(StorageProvider):
    """
    Local filesystem implementation of StorageProvider with directory sandboxing
    and path traversal protection (ADR-009). Uses native standard library asyncio.to_thread.
    """

    def __init__(self, base_directory: str = "./data/uploads"):
        self.base_dir = Path(base_directory).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_and_verify_path(self, storage_path: str) -> Path:
        """
        Guarantees that the target path cannot escape the base directory (Path Traversal Guard).
        """
        # Handle relative or absolute paths
        target_path = Path(storage_path)
        if not target_path.is_absolute():
            target_path = (self.base_dir / target_path).resolve()
        else:
            target_path = target_path.resolve()

        if not str(target_path).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected: '{storage_path}' is outside sandbox.")

        return target_path

    async def save_file(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Saves file bytes with a content-hashed prefix to guarantee deduplication and clean filenames.
        """
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        ext = Path(filename).suffix.lower()
        if not ext:
            ext = ".bin"

        stored_filename = f"{sha256[:16]}_{Path(filename).stem}{ext}"
        destination = self._resolve_and_verify_path(stored_filename)

        await asyncio.to_thread(destination.write_bytes, file_bytes)

        return str(destination)

    async def get_file_bytes(self, storage_path: str) -> bytes:
        """
        Reads and returns raw bytes from the sandbox.
        """
        target_path = self._resolve_and_verify_path(storage_path)
        if not target_path.exists():
            raise FileNotFoundError(f"File not found at storage path: {storage_path}")

        return await asyncio.to_thread(target_path.read_bytes)

    async def delete_file(self, storage_path: str) -> bool:
        """
        Deletes the target file from the sandbox.
        """
        try:
            target_path = self._resolve_and_verify_path(storage_path)
            if target_path.exists():
                await asyncio.to_thread(os.remove, target_path)
                return True
            return False
        except Exception:
            return False


    def get_file_url(self, storage_path: str) -> str:
        """
        Returns the sanitized string path.
        """
        return str(self._resolve_and_verify_path(storage_path))
