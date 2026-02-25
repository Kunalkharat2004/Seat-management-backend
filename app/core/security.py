"""
Authentication utility functions for password hashing, verification, and
secure token generation.

This module contains **only** stateless helper functions — no business logic,
no database access, no request/response handling.
"""

import hashlib
import secrets

from passlib.context import CryptContext

# ── Bcrypt hashing context ────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_MIN_PASSWORD_LENGTH = 8


# ── Password utilities ────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*.

    Raises
    ------
    ValueError
        If *password* is shorter than 8 characters.
    """
    if len(password) < _MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must be at least {_MIN_PASSWORD_LENGTH} characters long."
        )
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check *plain_password* against a bcrypt *hashed_password*."""
    return _pwd_context.verify(plain_password, hashed_password)


# ── Token utilities ───────────────────────────────────────────────

def generate_secure_token() -> str:
    """Return a cryptographically secure URL-safe token (32 random bytes)."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of *token*.

    Used to store a one-way hash of password-reset / invite tokens so the
    raw token is never persisted in the database.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
