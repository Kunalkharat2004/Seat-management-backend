import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, text
from sqlalchemy.dialects.postgresql import UUID, ENUM, TIMESTAMP
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

    # Nullable until the user sets their password via invite link
    password_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )

    # ── Role & status ─────────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        user_role_enum, nullable=False, server_default=text("'employee'")
    )
    status: Mapped[str] = mapped_column(
        user_status_enum, nullable=False, server_default=text("'active'")
    )

    # ── Invite & password-reset state ─────────────────────────────
    is_invite_sent: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        index=True,
    )
    # Store only the hashed token; the raw token is emailed and never persisted
    password_reset_token_hash: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None, index=True
    )
    password_reset_expires: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, default=None
    )

    # ── Timestamps (all timezone-aware) ───────────────────────────
    last_login_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # ── Relationships ─────────────────────────────────────────────
    bookings = relationship("Booking", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User {self.employee_id} – {self.name}>"
