"""Key Management Service (KMS) port."""

from __future__ import annotations

from typing import Protocol


class KMSPort(Protocol):
    """Port for encrypting and decrypting tenant data keys."""

    async def generate_data_key(self, tenant_id: str) -> tuple[bytes, bytes]:
        """Generate a new data key.

        Returns:
            Tuple of (plaintext_key, encrypted_key).
        """
        ...

    async def encrypt_data_key(self, tenant_id: str, plaintext_key: bytes) -> bytes:
        """Encrypt a data key for a specific tenant."""
        ...

    async def decrypt_data_key(self, tenant_id: str, encrypted_key: bytes) -> bytes:
        """Decrypt a data key for a specific tenant."""
        ...
