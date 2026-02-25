"""
Service layer for admin operations — employee creation and invite flow.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import generate_secure_token, hash_token
from app.models.user import User
from app.schemas.admin import CreateEmployeeRequest
from app.utils.email import send_invite_email

logger = logging.getLogger(__name__)


async def create_employee_and_send_invite(
    db: Session,
    employee_data: CreateEmployeeRequest,
) -> dict:
    """Create a new employee record and send a password-setup invite email.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session (from ``get_db``).
    employee_data : CreateEmployeeRequest
        Validated request body.

    Returns
    -------
    dict
        ``{"message": "...", "employee_id": "..."}``

    Raises
    ------
    HTTPException (409)
        If ``employee_id`` or ``email`` already exists.
    """

    # ── Uniqueness checks ─────────────────────────────────────────
    if db.query(User).filter(User.employee_id == employee_data.employee_id).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee ID '{employee_data.employee_id}' already exists.",
        )

    if db.query(User).filter(User.email == employee_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{employee_data.email}' already exists.",
        )

    # ── Create user row ───────────────────────────────────────────
    raw_token = generate_secure_token()

    user = User(
        employee_id=employee_data.employee_id,
        name=employee_data.name,
        email=employee_data.email,
        role=employee_data.role,
        password_hash=None,
        must_change_password=True,
        is_invite_sent=False,
        password_reset_token_hash=hash_token(raw_token),
        password_reset_expires=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # ── Send invite email ─────────────────────────────────────────
    await send_invite_email(to_email=employee_data.email, token=raw_token)

    user.is_invite_sent = True
    db.commit()

    logger.info("Employee %s created and invite sent.", employee_data.employee_id)

    return {
        "message": "Employee created and invite email sent.",
        "employee_id": employee_data.employee_id,
    }
