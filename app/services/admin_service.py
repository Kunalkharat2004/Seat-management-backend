"""
Service layer for admin operations — employee creation and invite flow.
"""

import csv
import io
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import generate_secure_token, hash_token
from app.models.user import User
from app.schemas.admin import CreateEmployeeRequest
from app.utils.email import send_invite_email

logger = logging.getLogger(__name__)

_REQUIRED_CSV_COLUMNS = {"employee_id", "name", "email", "role"}


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


async def bulk_create_employees_from_csv(
    db: Session,
    file: UploadFile,
) -> dict:
    """Parse a CSV file and create employee records row-by-row.

    Each row is processed in its own transaction so that a single
    failure never rolls back the entire batch.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session.
    file : UploadFile
        Uploaded CSV with columns ``employee_id,name,email,role``.

    Returns
    -------
    dict
        Counts: ``total_rows``, ``successful_creations``,
        ``skipped_rows``, ``failed_rows``.
    """

    # ── Read & parse CSV ──────────────────────────────────────────
    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8-sig")  # handles optional BOM
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not valid UTF-8.",
        )

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None or not _REQUIRED_CSV_COLUMNS.issubset(
        {col.strip().lower() for col in reader.fieldnames}
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"CSV must contain columns: {', '.join(sorted(_REQUIRED_CSV_COLUMNS))}. "
                f"Found: {reader.fieldnames}"
            ),
        )

    # ── Process rows ──────────────────────────────────────────────
    total = 0
    created = 0
    skipped = 0
    failed = 0

    for row in reader:
        total += 1
        emp_id = (row.get("employee_id") or "").strip()
        name = (row.get("name") or "").strip()
        email = (row.get("email") or "").strip()
        role = (row.get("role") or "employee").strip() or "employee"

        if not emp_id or not name or not email:
            logger.warning("Row %d: missing required field(s), skipping.", total)
            failed += 1
            continue

        # Skip duplicates
        if db.query(User).filter(User.employee_id == emp_id).first():
            logger.info("Row %d: employee_id '%s' already exists, skipping.", total, emp_id)
            skipped += 1
            continue

        try:
            raw_token = generate_secure_token()

            user = User(
                employee_id=emp_id,
                name=name,
                email=email,
                role=role,
                password_hash=None,
                must_change_password=True,
                is_invite_sent=False,
                password_reset_token_hash=hash_token(raw_token),
                password_reset_expires=datetime.now(timezone.utc) + timedelta(hours=24),
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            # Send invite email
            await send_invite_email(to_email=email, token=raw_token)

            user.is_invite_sent = True
            db.commit()

            created += 1
            logger.info("Row %d: employee '%s' created and invite sent.", total, emp_id)

        except Exception:
            db.rollback()
            failed += 1
            logger.exception("Row %d: failed to create employee '%s'.", total, emp_id)

    return {
        "total_rows": total,
        "successful_creations": created,
        "skipped_rows": skipped,
        "failed_rows": failed,
    }


async def update_user_status(
    db: Session,
    employee_id: str,
    new_status: str,
    current_admin: User,
) -> dict:
    """Activate or deactivate an employee account.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session.
    employee_id : str
        The employee_id of the target user.
    new_status : str
        One of ``"active"`` or ``"inactive"``.
    current_admin : User
        The authenticated admin performing the action.

    Returns
    -------
    dict
        Confirmation message with updated employee_id and status.

    Raises
    ------
    HTTPException (404)
        If the target user does not exist.
    HTTPException (400)
        If the admin tries to change their own status.
    """

    # ── Fetch target user ─────────────────────────────────────────
    user = db.query(User).filter(User.employee_id == employee_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{employee_id}' not found.",
        )

    # ── Self-modification guard ───────────────────────────────────
    if current_admin.id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot change their own status.",
        )

    # ── Update & commit ───────────────────────────────────────────
    user.status = new_status
    db.commit()

    logger.info(
        "Admin '%s' set employee '%s' to '%s'.",
        current_admin.employee_id,
        employee_id,
        new_status,
    )

    return {
        "message": f"Employee status updated to '{new_status}'.",
        "employee_id": employee_id,
        "status": new_status,
    }
