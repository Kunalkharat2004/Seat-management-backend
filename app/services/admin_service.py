"""
Service layer for admin operations — employee CRUD and invite flow.
"""

import csv
import io
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.config import settings
from app.core.security import generate_secure_token, hash_token
from app.models.user import User
from app.schemas.admin import (
    CreateEmployeeRequest,
    EmployeeResponse,
    EmployeeUpdateRequest,
    PaginatedEmployeeResponse,
)
from app.types.user_types import (
    ROLE_ADMIN,
    ROLE_EMPLOYEE,
    STATUS_ACTIVE,
    STATUS_INACTIVE,
)
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)

_REQUIRED_CSV_COLUMNS = {"employee_id", "name", "email", "role"}

# Fields that must never be touched via the generic update endpoint.
_PROTECTED_FIELDS = {
    "password_hash",
    "password_reset_token_hash",
    "password_reset_expires",
    "must_change_password",
}


# ── Create ────────────────────────────────────────────────────────


async def create_employee_and_send_invite(
    db: Session,
    employee_data: CreateEmployeeRequest,
) -> dict:
    """Create a new employee record and send a password-setup invite email.

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

    # if settings.APP_ENV == "development":
    #     print(f"\n[DEV MODE] Invite token for {employee_data.email}: {raw_token}\n")

    db.add(user)
    db.commit()
    db.refresh(user)

    # ── Send invite email ─────────────────────────────────────────
    email_service = EmailService()
    try:
        email_sent = await email_service.send_invite_email(to_email=employee_data.email, invite_token=raw_token)
        if email_sent:
            user.is_invite_sent = True
            db.commit()
    except Exception:
        logger.exception("Email sending failed for %s", user.employee_id)

    logger.info("Employee %s created and invite sent.", employee_data.employee_id)

    return {
        "message": "Employee created and invite email sent.",
        "employee_id": employee_data.employee_id,
    }


# ── Bulk create ───────────────────────────────────────────────────


async def bulk_create_employees_from_csv(
    db: Session,
    file: UploadFile,
) -> dict:
    """Parse a CSV file and create employee records row-by-row.

    Each row is processed in its own transaction so that a single
    failure never rolls back the entire batch.
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
        role = (row.get("role") or ROLE_EMPLOYEE).strip() or ROLE_EMPLOYEE

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

            # if settings.APP_ENV == "development":
            #     print(f"[DEV MODE] Bulk invite token for {email}: {raw_token}")

            db.add(user)
            db.commit()
            db.refresh(user)

            # Send invite email
            email_service = EmailService()
            try:
                email_sent = await email_service.send_invite_email(to_email=email, invite_token=raw_token)
                if email_sent:
                    user.is_invite_sent = True
                    db.commit()
            except Exception:
                logger.exception("Email sending failed for %s", emp_id)

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


# ── Read (list + single) ─────────────────────────────────────────


async def get_employees(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
    status_filter: str | None = None,
    role_filter: str | None = None,
) -> PaginatedEmployeeResponse:
    """Return a filtered, paginated list of employees.

    Parameters
    ----------
    search : str, optional
        Case-insensitive partial match on employee_id, name, or email.
    status_filter : str, optional
        Exact match on status (STATUS_ACTIVE / STATUS_INACTIVE).
    role_filter : str, optional
        Exact match on role (ROLE_EMPLOYEE / ROLE_ADMIN).
    """

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    if page_size > 100:
        page_size = 100

    # ── Validation ────────────────────────────────────────────────
    if status_filter and status_filter not in [STATUS_ACTIVE, STATUS_INACTIVE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {status_filter}",
        )
    if role_filter and role_filter not in [ROLE_EMPLOYEE, ROLE_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {role_filter}",
        )

    # ── Build dynamic query ───────────────────────────────────────
    query = db.query(User)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.employee_id.ilike(pattern),
                User.name.ilike(pattern),
                User.email.ilike(pattern),
            )
        )

    if status_filter:
        query = query.filter(User.status == status_filter)

    if role_filter:
        query = query.filter(User.role == role_filter)

    # ── Count AFTER filters, then paginate ────────────────────────
    total = query.count()
    offset = (page - 1) * page_size

    users = (
        query
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return PaginatedEmployeeResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[EmployeeResponse.model_validate(u) for u in users],
    )


async def get_employee_by_id(
    db: Session,
    user_id: str,
) -> EmployeeResponse:
    """Fetch a single employee by primary-key ``id`` (UUID as string).

    Raises
    ------
    HTTPException (404)
        If no user exists with the given ``id``.
    """

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{user_id}' not found.",
        )

    return EmployeeResponse.model_validate(user)


# ── Update ────────────────────────────────────────────────────────


async def update_employee(
    db: Session,
    user_id: str,
    update_data: EmployeeUpdateRequest,
) -> EmployeeResponse:
    """Update allowed fields for the employee with the given primary-key ``id``.

    Only non-``None`` fields from the request body are applied.
    Password-related fields are never modified.

    Raises
    ------
    HTTPException (404)
        If no user exists with the given ``id``.
    """

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{user_id}' not found.",
        )

    # Apply only the fields that were explicitly provided.
    update_fields = update_data.model_dump(exclude_unset=True)

    for field, value in update_fields.items():
        if field in _PROTECTED_FIELDS:
            continue
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    logger.info("Employee id='%s' updated.", user_id)

    return EmployeeResponse.model_validate(user)


# ── Delete (soft) ─────────────────────────────────────────────────


async def delete_employee(
    db: Session,
    user_id: str,
    current_admin: User,
) -> dict:
    """Soft-delete an employee by setting ``status = STATUS_INACTIVE``.

    Looks up the employee by primary-key ``id`` (UUID as string).

    Raises
    ------
    HTTPException (404)
        If the target user does not exist.
    HTTPException (400)
        If the admin tries to deactivate themselves.
    """

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee '{user_id}' not found.",
        )

    if str(current_admin.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin cannot deactivate themselves.",
        )

    user.status = STATUS_INACTIVE
    db.commit()

    logger.info(
        "Admin '%s' deactivated employee id='%s'.",
        current_admin.employee_id,
        user_id,
    )

    return {
        "message": f"Employee '{user.employee_id}' has been deactivated.",
        "id": user_id,
        "status": STATUS_INACTIVE,
    }
