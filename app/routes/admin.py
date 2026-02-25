"""Admin routes — employee management."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import BulkUploadResponse, CreateEmployeeRequest, UserStatusUpdateRequest
from app.services.admin_service import (
    bulk_create_employees_from_csv,
    create_employee_and_send_invite,
    update_user_status,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users", status_code=201)
async def create_employee(
    body: CreateEmployeeRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Create a new employee and send a password-setup invite email."""
    return await create_employee_and_send_invite(db, body)


@router.post("/users/bulk-upload", status_code=200, response_model=BulkUploadResponse)
async def bulk_upload_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Bulk-create employees from a CSV file.

    Expected CSV columns: ``employee_id,name,email,role``
    """
    # Basic content-type / extension guard
    if file.content_type not in ("text/csv", "application/vnd.ms-excel") and not (
        file.filename or ""
    ).lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a CSV.",
        )

    return await bulk_create_employees_from_csv(db, file)


@router.patch("/users/status")
async def update_employee_status(
    emp_id: str,
    body: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Activate or deactivate an employee account."""
    return await update_user_status(db, emp_id, body.status, admin)
