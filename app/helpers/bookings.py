from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User

def _resolve_user(db: Session, employee_id: str) -> User:
    """Load the full User ORM object from the JWT-supplied employee_id."""
    user = db.query(User).filter(User.employee_id == employee_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
        )
    return user