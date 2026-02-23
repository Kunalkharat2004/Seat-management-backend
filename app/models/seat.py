import uuid
from datetime import datetime

from sqlalchemy import String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Seat(Base):
    __tablename__ = "seats"

    # ── Primary key ───────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ── Seat info ─────────────────────────────────────────────────
    seat_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )

    # ── Timestamps ────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────
    bookings = relationship("Booking", back_populates="seat", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Seat {self.seat_number}>"
