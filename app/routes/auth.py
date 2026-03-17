"""Authentication routes — login, set-password, and forgot-password."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    GenericMessageResponse,
    LoginRequest,
    LoginResponse,
    SetPasswordRequest,
    UserResponse,
)
from app.services.auth_service import forgot_password, get_auth_user, login, set_password
from app.core.jwt import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    db: Session = Depends(get_db),
    employee_id: str = Depends(get_current_user),
):
    """Return the currently authenticated user's profile."""
    return await get_auth_user(db, employee_id)


@router.post("/login", response_model=LoginResponse)
async def login_route(
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate an employee and return a JWT access token."""
    return await login(db, body.employee_id, body.password)


@router.post("/logout")
async def logout_route(
    _employee_id: str = Depends(get_current_user),
):
    """Logout the current user.

    Stateless — the frontend is responsible for discarding the token.
    """
    return {"message": "Logged out successfully"}


@router.post("/set-password")
async def set_password_route(
    body: SetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Set password using an invite/reset token."""
    return await set_password(db, body.token, body.new_password)


@router.post("/forgot-password", response_model=GenericMessageResponse)
async def forgot_password_route(
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """Request a password-reset email. Always returns 200."""
    return await forgot_password(db, body.email)
