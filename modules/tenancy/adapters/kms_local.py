"""Local KMS adapter for development."""

from __future__ import annotations

import base64
import os
from typing import ClassVar

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from modules.tenancy.domain.settings import get_settings
from modules.tenancy.ports.kms import KMSPort


class LocalKMSAdapter(KMSPort):
    """Local KMS using a single master key from environment variables.
    
    WARNING: For development only. In production, use AWS KMS or GCP Cloud KMS.
    """

    def __init__(self, master_key_b64: str | None = None) -> None:
        if master_key_b64 is None:
            master_key_b64 = get_settings().encryption_master_key
        
        # Pad if missing, must decode to 32 bytes for AES-256
        try:
            self._master_key = base64.b64decode(master_key_b64)
            if len(self._master_key) not in (16, 24, 32):
                # Fallback for dev if invalid key provided
                self._master_key = os.urandom(32)
        except Exception:
            self._master_key = os.urandom(32)
            
        self._aead = AESGCM(self._master_key)

    async def generate_data_key(self, tenant_id: str) -> tuple[bytes, bytes]:
        """Generate a new 32-byte data key and encrypt it with the master key."""
        plaintext_key = os.urandom(32)
        # Nonce for AES-GCM is 12 bytes
        nonce = os.urandom(12)
        # Include tenant_id as associated data to bind the key
        aad = tenant_id.encode()
        encrypted_key_payload = self._aead.encrypt(nonce, plaintext_key, aad)
        
        # Prepend nonce to the encrypted payload
        encrypted_key = nonce + encrypted_key_payload
        return plaintext_key, encrypted_key

    async def encrypt_data_key(self, tenant_id: str, plaintext_key: bytes) -> bytes:
        """Encrypt an existing data key."""
        nonce = os.urandom(12)
        aad = tenant_id.encode()
        encrypted_key_payload = self._aead.encrypt(nonce, plaintext_key, aad)
        return nonce + encrypted_key_payload

    async def decrypt_data_key(self, tenant_id: str, encrypted_key: bytes) -> bytes:
        """Decrypt a data key."""
        nonce = encrypted_key[:12]
        payload = encrypted_key[12:]
        aad = tenant_id.encode()
        return self._aead.decrypt(nonce, payload, aad)
