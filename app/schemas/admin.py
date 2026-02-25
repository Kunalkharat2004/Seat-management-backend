"""Pydantic schemas for admin endpoints."""

from pydantic import BaseModel, EmailStr


class CreateEmployeeRequest(BaseModel):
    """Body for POST /admin/users."""

    employee_id: str
    name: str
    email: EmailStr
    role: str = "employee"
