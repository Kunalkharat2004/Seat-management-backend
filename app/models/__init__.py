# Import all models so that Base.metadata is fully populated
# when Alembic or create_all() runs.
from app.models.user import User          # noqa: F401
from app.models.seat import Seat          # noqa: F401
from app.models.booking import Booking    # noqa: F401

from app.db.session import Base           # noqa: F401

__all__ = ["User", "Seat", "Booking", "Base"]
