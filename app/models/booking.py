import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


# ── PostgreSQL ENUM for booking status ────────────────────────────
booking_status_enum = ENUM(
    "confirmed", "checked_in", "expired", "cancelled",
    name="booking_status",
    create_type=True,
)


class Booking(Base):
    __tablename__ = "bookings"

    # ── Table-level constraints ───────────────────────────────────
    __table_args__ = (
        UniqueConstraint("user_id", "booking_date", name="uq_user_booking_date"),
        UniqueConstraint("seat_id", "booking_date", name="uq_seat_booking_date"),
    )

    # ── Primary key ───────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ── Foreign keys ──────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    seat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("seats.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # ── Booking data ──────────────────────────────────────────────
    booking_date: Mapped[date] = mapped_column(
        Date, index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        booking_status_enum,
        nullable=False,
        server_default=text("'confirmed'"),
    )
    check_in_time: Mapped[datetime | None] = mapped_column(
        nullable=True, default=None
    )
    cancelled_by: Mapped[str | None] = mapped_column(
        String(50), nullable=True, default=None
    )

    # ── Timestamps ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────
    user = relationship("User", back_populates="bookings", lazy="joined")
    seat = relationship("Seat", back_populates="bookings", lazy="joined")

    def __repr__(self) -> str:
        return f"<Booking {self.id} | seat={self.seat_id} date={self.booking_date} status={self.status}>"
