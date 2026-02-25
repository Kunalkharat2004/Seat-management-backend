"""Pydantic schemas for admin endpoints."""

from typing import Literal

from pydantic import BaseModel, EmailStr


class CreateEmployeeRequest(BaseModel):
    """Body for POST /admin/users."""

    employee_id: str
    name: str
    email: EmailStr
    role: str = "employee"


class BulkUploadResponse(BaseModel):
    """Response for POST /admin/users/bulk-upload."""

    total_rows: int
    successful_creations: int
    skipped_rows: int
    failed_rows: int


class UserStatusUpdateRequest(BaseModel):
    """Body for PATCH /admin/users/{employee_id}/status."""

    status: Literal["active", "inactive"]
