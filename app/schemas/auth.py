"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Body for POST /auth/login."""

    employee_id: str
    password: str


class LoginResponse(BaseModel):
    """Response from POST /auth/login."""

    access_token: str
    token_type: str = "bearer"
    role: str
