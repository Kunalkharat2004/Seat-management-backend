"""Authentication routes — login."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login_route(
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate an employee and return a JWT access token."""
    return await login(db, body.employee_id, body.password)
