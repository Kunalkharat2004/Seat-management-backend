"""Admin routes — employee CRUD and management."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import (
    BulkUploadResponse,
    CreateEmployeeRequest,
    EmployeeResponse,
    EmployeeUpdateRequest,
    PaginatedEmployeeResponse,
)
from app.services.admin_service import (
    bulk_create_employees_from_csv,
    create_employee_and_send_invite,
    delete_employee,
    get_employee_by_id,
    get_employees,
    update_employee,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Create ────────────────────────────────────────────────────────


@router.post("/employees", status_code=201)
async def create_employee_route(
    body: CreateEmployeeRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Create a new employee and send a password-setup invite email."""
    return await create_employee_and_send_invite(db, body)


@router.post("/employees/bulk-upload", status_code=200, response_model=BulkUploadResponse)
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


# ── Read ──────────────────────────────────────────────────────────


@router.get("/employees", response_model=PaginatedEmployeeResponse)
async def list_employees(
    search: str | None = Query(None, description="Search employee_id, name, or email"),
    status: Literal["active", "inactive"] | None = Query(None, description="Filter by status"),
    role: Literal["employee", "admin"] | None = Query(None, description="Filter by role"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Return a filtered, paginated list of all employees."""
    return await get_employees(db, page, page_size, search, status, role)


@router.get("/employees/{id}", response_model=EmployeeResponse)
async def get_employee_route(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Return a single employee by primary-key id (UUID)."""
    return await get_employee_by_id(db, str(id))


# ── Update ────────────────────────────────────────────────────────


@router.patch("/employees/{id}", response_model=EmployeeResponse)
async def update_employee_route(
    id: uuid.UUID,
    body: EmployeeUpdateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Update an employee's profile fields (lookup by primary-key id)."""
    return await update_employee(db, str(id), body)


# ── Delete (soft) ─────────────────────────────────────────────────


@router.delete("/employees/{id}")
async def delete_employee_route(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user),
):
    """Soft-delete (deactivate) an employee (lookup by primary-key id)."""
    return await delete_employee(db, str(id), admin)
