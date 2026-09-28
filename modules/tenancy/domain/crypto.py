"""Cryptography domain logic for PII protection.

Handles envelope encryption for data and HMAC keyed hashing for lookups.
"""

from __future__ import annotations

import base64
import hmac
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from modules.tenancy.domain.settings import get_settings


class CryptoService:
    """Service for encrypting/decrypting PII and generating lookup hashes."""

    @staticmethod
    def encrypt_value(plaintext: str, data_key: bytes) -> bytes:
        """Encrypt a string value using AES-GCM with the given data key.
        
        Args:
            plaintext: The string to encrypt.
            data_key: The 32-byte plaintext data key.
            
        Returns:
            The raw bytes of the nonce + ciphertext + tag.
        """
        aead = AESGCM(data_key)
        nonce = os.urandom(12)
        ciphertext = aead.encrypt(nonce, plaintext.encode("utf-8"), None)
        return nonce + ciphertext

    @staticmethod
    def decrypt_value(encrypted_data: bytes, data_key: bytes) -> str:
        """Decrypt a value using AES-GCM with the given data key.
        
        Args:
            encrypted_data: The raw bytes containing nonce + ciphertext + tag.
            data_key: The 32-byte plaintext data key.
            
        Returns:
            The decrypted string.
        """
        aead = AESGCM(data_key)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        plaintext = aead.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")

    @staticmethod
    def hash_value(plaintext: str, tenant_id: str) -> bytes:
        """Create a deterministic keyed hash for lookups.
        
        This allows searching for exact matches of PII (like a phone number)
        without storing the plaintext or a decryptable ciphertext in a lookup index.
        We use HMAC-SHA256 with the master key + tenant_id as the key.
        
        Args:
            plaintext: The string to hash (e.g. a normalized phone number).
            tenant_id: The tenant ID to namespace the hash.
            
        Returns:
            The raw bytes of the hash.
        """
        master_key_b64 = get_settings().encryption_master_key
        try:
            master_key = base64.b64decode(master_key_b64)
        except Exception:
            master_key = master_key_b64.encode("utf-8")
            
        # Key is derived from master key and tenant ID to ensure isolation
        hmac_key = hmac.new(master_key, tenant_id.encode("utf-8"), hashlib.sha256).digest()
        
        # Hash the actual value
        h = hmac.new(hmac_key, plaintext.encode("utf-8"), hashlib.sha256)
        return h.digest()
