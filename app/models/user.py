import uuid
from datetime import datetime

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


# ── PostgreSQL ENUM types ─────────────────────────────────────────
user_role_enum = ENUM("employee", "admin", name="user_role", create_type=True)
user_status_enum = ENUM("active", "inactive", name="user_status", create_type=True)


class User(Base):
    __tablename__ = "users"

    # ── Primary key ───────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ── Identity ──────────────────────────────────────────────────
    employee_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    # ── Role & status ─────────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        user_role_enum, nullable=False, server_default=text("'employee'")
    )
    status: Mapped[str] = mapped_column(
        user_status_enum, nullable=False, server_default=text("'active'")
    )

    # ── Timestamps ────────────────────────────────────────────────
    last_login_at: Mapped[datetime | None] = mapped_column(
        nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────
    bookings = relationship("Booking", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.employee_id} – {self.name}>"
