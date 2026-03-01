"""Pydantic schemas for authentication endpoints."""

import uuid
from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    """Body for POST /auth/login."""

    employee_id: str
    password: str


class LoginResponse(BaseModel):
    """Response from POST /auth/login."""

    access_token: str
    token_type: str = "bearer"
    role: str


class SetPasswordRequest(BaseModel):
    """Body for POST /auth/set-password."""

    token: str
    new_password: str


class UserResponse(BaseModel):
    """Basic user information for /auth/me."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: str
    name: str
    email: str
    role: str
    status: str
