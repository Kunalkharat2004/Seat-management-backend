"""Pydantic schemas for admin endpoints."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.types.user_types import ROLE_ADMIN, ROLE_EMPLOYEE, STATUS_ACTIVE, STATUS_INACTIVE


class CreateEmployeeRequest(BaseModel):
    """Body for POST /admin/users."""

    employee_id: str
    name: str
    email: EmailStr
    role: str = ROLE_EMPLOYEE


class BulkUploadResponse(BaseModel):
    """Response for POST /admin/users/bulk-upload."""

    total_rows: int
    successful_creations: int
    skipped_rows: int
    failed_rows: int


# ── CRUD schemas ──────────────────────────────────────────────────


class EmployeeResponse(BaseModel):
    """Safe employee representation — excludes sensitive fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: str
    name: str
    email: str
    role: str
    status: str
    created_at: datetime


class EmployeeUpdateRequest(BaseModel):
    """Body for PATCH /admin/users/{employee_id}."""

    name: str | None = None
    email: EmailStr | None = None
    role: Literal["employee", "admin"] | None = None  # type: ignore[assignment]
    status: Literal["active", "inactive"] | None = None  # type: ignore[assignment]


class PaginatedEmployeeResponse(BaseModel):
    """Paginated list of employees."""

    total: int
    page: int
    page_size: int
    items: list[EmployeeResponse]
