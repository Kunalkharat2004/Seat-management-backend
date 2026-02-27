"""
FastAPI dependencies for role-based access control.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.jwt import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.types.user_types import ROLE_ADMIN


async def get_current_admin_user(
    employee_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the current user and verify they have the **admin** role.

    Returns the full ``User`` ORM object so the route/service can access
    any user attribute without an extra query.

    Raises
    ------
    HTTPException (403)
        If the authenticated user is not an admin.
    HTTPException (401)
        If the user record no longer exists in the database.
    """
    user = db.query(User).filter(User.employee_id == employee_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )

    if user.role != ROLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )

    return user
