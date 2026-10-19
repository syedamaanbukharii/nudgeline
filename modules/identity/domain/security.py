"""Password hashing and session tokens."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
_ALGORITHM = "HS256"
MIN_PASSWORD_LENGTH = 10


def hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


# A real hash to verify against when the email is unknown, so login timing doesn't leak which emails exist.
DUMMY_HASH = _hasher.hash("dummy-password-for-timing")


@dataclass(frozen=True)
class TokenClaims:
    user_id: uuid.UUID
    tenant_id: uuid.UUID


def issue_token(claims: TokenClaims, secret: str, ttl_minutes: int) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(claims.user_id),
        "tid": str(claims.tenant_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=_ALGORITHM)


def read_token(token: str, secret: str) -> TokenClaims | None:
    """Return the claims of a valid, unexpired token, or None."""
    try:
        payload = jwt.decode(token, secret, algorithms=[_ALGORITHM], options={"require": ["sub", "tid", "exp"]})
        return TokenClaims(user_id=uuid.UUID(payload["sub"]), tenant_id=uuid.UUID(payload["tid"]))
    except (jwt.InvalidTokenError, ValueError, KeyError):
        return None
