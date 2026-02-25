"""
JWT utility functions for token creation, verification, and a FastAPI
dependency that extracts the current user from an Authorization header.

This module contains **only** stateless JWT helpers — no database access,
no business logic.
"""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings

# ── OAuth2 scheme (extracts Bearer token from Authorization header) ──
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Token creation ────────────────────────────────────────────────

def create_access_token(data: dict) -> str:
    """Create a signed JWT with an ``exp`` claim.

    Parameters
    ----------
    data : dict
        Payload to encode.  Should include ``"sub"`` with the
        employee_id of the authenticated user.

    Returns
    -------
    str
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


# ── Token verification ───────────────────────────────────────────

def verify_access_token(token: str) -> dict:
    """Decode and validate a JWT.

    Parameters
    ----------
    token : str
        Encoded JWT string.

    Returns
    -------
    dict
        Decoded payload.

    Raises
    ------
    jose.JWTError
        If the token is invalid, expired, or tampered with.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


# ── FastAPI dependency ────────────────────────────────────────────

async def get_current_user(token: str = Depends(_oauth2_scheme)) -> str:
    """FastAPI dependency that returns the ``employee_id`` of the caller.

    Extracts the Bearer token from the ``Authorization`` header, decodes
    it, and returns the ``sub`` claim (which should be the employee_id).

    Raises
    ------
    HTTPException (401)
        If the token is missing, expired, or does not contain a valid
        ``sub`` claim.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_access_token(token)
        employee_id: str | None = payload.get("sub")
        if employee_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return employee_id
