"""
Service layer for authentication — login and set-password flows.
"""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token
from app.core.security import hash_password, hash_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginResponse
from app.types.user_types import STATUS_ACTIVE

logger = logging.getLogger(__name__)


async def login(db: Session, employee_id: str, password: str) -> LoginResponse:
    """Authenticate an employee and return a JWT.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session.
    employee_id : str
        Corporate employee ID.
    password : str
        Plain-text password to verify.

    Returns
    -------
    LoginResponse
        Contains ``access_token``, ``token_type``, and ``role``.

    Raises
    ------
    HTTPException (401)
        If the user does not exist or the password is wrong.
    HTTPException (403)
        If the account is deactivated.
    HTTPException (400)
        If the user has not set a password yet (invite not completed).
    """
    # Generic message to prevent user enumeration
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ── Look up user ──────────────────────────────────────────────
    user = db.query(User).filter(User.employee_id == employee_id).first()

    if user is None:
        raise invalid_credentials

    # ── Account status check ──────────────────────────────────────
    if user.status != STATUS_ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact admin.",
        )

    # ── Password-not-set check ────────────────────────────────────
    if user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account setup not completed.",
        )

    # ── Password verification ─────────────────────────────────────
    if not verify_password(password, user.password_hash):
        raise invalid_credentials

    # ── Issue token ───────────────────────────────────────────────
    access_token = create_access_token({"sub": user.employee_id})

    # Update last_login_at
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    logger.info("User %s logged in.", employee_id)

    return LoginResponse(
        access_token=access_token,
        role=user.role,
    )


async def set_password(db: Session, token: str, new_password: str) -> dict:
    """Validate an invite/reset token and set the user's password.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session.
    token : str
        Raw (unhashed) invite token from the email link.
    new_password : str
        Plain-text password chosen by the user.

    Returns
    -------
    dict
        ``{"message": "..."}``

    Raises
    ------
    HTTPException (400)
        If the token is invalid or expired.
    """

    # ── Look up user by hashed token ──────────────────────────────
    token_hash = hash_token(token)
    user = (
        db.query(User)
        .filter(User.password_reset_token_hash == token_hash)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already-used token.",
        )

    # ── Expiry check ──────────────────────────────────────────────
    if (
        user.password_reset_expires is None
        or user.password_reset_expires < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token has expired. Please request a new invite.",
        )

    # ── Set password & clear token fields ─────────────────────────
    user.password_hash = hash_password(new_password)
    user.password_reset_token_hash = None
    user.password_reset_expires = None
    user.must_change_password = False

    db.commit()

    logger.info("Password set for user %s.", user.employee_id)

    return {"message": "Password set successfully."}


async def get_auth_user(db: Session, employee_id: str) -> User:
    """Look up a user by employee_id.

    Raises
    ------
    HTTPException (401)
        If the user no longer exists.
    """
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )
    return user
