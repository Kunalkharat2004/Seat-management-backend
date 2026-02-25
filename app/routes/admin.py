"""Admin routes — employee management."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.admin import CreateEmployeeRequest
from app.services.admin_service import create_employee_and_send_invite

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users", status_code=201)
async def create_employee(
    body: CreateEmployeeRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Create a new employee and send a password-setup invite email."""
    return await create_employee_and_send_invite(db, body)
