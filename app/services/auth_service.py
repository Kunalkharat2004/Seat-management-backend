"""
Service layer for authentication — login flow.
"""

import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token
from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import LoginResponse

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
        detail="Invalid employee ID or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # ── Look up user ──────────────────────────────────────────────
    user = db.query(User).filter(User.employee_id == employee_id).first()

    if user is None:
        raise invalid_credentials

    # ── Account status check ──────────────────────────────────────
    if user.status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact your administrator.",
        )

    # ── Password-not-set check ────────────────────────────────────
    if user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password not set. Please complete your invite first.",
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
