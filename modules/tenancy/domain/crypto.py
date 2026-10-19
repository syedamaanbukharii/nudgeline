"""Envelope encryption for personal data and keyed hashes for lookups."""

from __future__ import annotations

import hashlib
import hmac
import os
from collections.abc import Mapping

import orjson
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt_value(plaintext: str, data_key: bytes) -> bytes:
    """AES-GCM encrypt; returns nonce + ciphertext + tag."""
    nonce = os.urandom(12)
    return nonce + AESGCM(data_key).encrypt(nonce, plaintext.encode("utf-8"), None)


def decrypt_value(encrypted: bytes, data_key: bytes) -> str:
    """Reverse of :func:`encrypt_value`."""
    return AESGCM(data_key).decrypt(encrypted[:12], encrypted[12:], None).decode("utf-8")


def encrypt_json(value: Mapping[str, object], data_key: bytes) -> bytes:
    return encrypt_value(orjson.dumps(value).decode(), data_key)


def decrypt_json(encrypted: bytes, data_key: bytes) -> dict[str, object]:
    result = orjson.loads(decrypt_value(encrypted, data_key))
    if not isinstance(result, dict):
        raise ValueError("encrypted payload is not an object")
    return result


def lookup_hash(value: str, tenant_id: str, master_key: bytes) -> bytes:
    """Deterministic HMAC-SHA256 keyed per tenant, for exact-match lookups (phone, DNC)."""
    tenant_key = hmac.new(master_key, tenant_id.encode(), hashlib.sha256).digest()
    return hmac.new(tenant_key, value.encode(), hashlib.sha256).digest()
