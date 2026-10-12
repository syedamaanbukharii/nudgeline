"""Local KMS adapter: wraps tenant data keys with a master key from settings."""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from modules.tenancy.domain.settings import get_settings
from modules.tenancy.ports.kms import KMSPort


def load_master_key() -> bytes:
    """Return the 32-byte master key.

    Outside development a valid base64 32-byte key is required. In development a
    missing key falls back to one derived from SECRET_KEY, so restarts keep working.
    """
    settings = get_settings()
    raw = settings.encryption_master_key
    if raw:
        try:
            key = base64.b64decode(raw, validate=True)
        except ValueError as exc:
            raise RuntimeError("ENCRYPTION_MASTER_KEY must be base64") from exc
        if len(key) != 32:
            raise RuntimeError("ENCRYPTION_MASTER_KEY must decode to 32 bytes")
        return key
    if settings.environment in ("development", "test"):
        return hashlib.sha256(f"dev-master-key:{settings.secret_key}".encode()).digest()
    raise RuntimeError("ENCRYPTION_MASTER_KEY is required outside development")


class LocalKMSAdapter(KMSPort):
    """Envelope encryption with a single master key. Swap for a cloud KMS in production."""

    def __init__(self, master_key: bytes | None = None) -> None:
        self._aead = AESGCM(master_key or load_master_key())

    async def generate_data_key(self, tenant_id: str) -> tuple[bytes, bytes]:
        plaintext_key = os.urandom(32)
        return plaintext_key, await self.encrypt_data_key(tenant_id, plaintext_key)

    async def encrypt_data_key(self, tenant_id: str, plaintext_key: bytes) -> bytes:
        nonce = os.urandom(12)
        return nonce + self._aead.encrypt(nonce, plaintext_key, tenant_id.encode())

    async def decrypt_data_key(self, tenant_id: str, encrypted_key: bytes) -> bytes:
        return self._aead.decrypt(encrypted_key[:12], encrypted_key[12:], tenant_id.encode())
