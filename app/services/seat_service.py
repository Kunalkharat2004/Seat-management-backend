"""
Service layer for seat operations — listing and availability.
"""

import logging
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.seat import Seat
from app.services.booking_service import validate_booking_date
from app.types.booking_status import CHECKED_IN, CONFIRMED

logger = logging.getLogger(__name__)


# ── List all seats ────────────────────────────────────────────────


async def get_all_seats(db: Session) -> list[dict]:
    """Return all seats ordered by seat_number ASC.

    Returns minimal fields: id, seat_number.
    """
    seats = (
        db.query(Seat.id, Seat.seat_number)
        .order_by(Seat.seat_number.asc())
        .all()
    )

    return [
        {"id": str(row.id), "seat_number": row.seat_number}
        for row in seats
    ]


# ── Seat availability ────────────────────────────────────────────


async def get_seat_availability(
    db: Session,
    booking_date: date,
) -> list[dict]:
    """Return all seats with their availability status for a given date.

    Uses a single LEFT JOIN query to determine availability:
      - ``available``   — no active booking exists for the seat on that date
      - ``confirmed``   — a confirmed booking exists
      - ``checked_in``  — a checked-in booking exists

    Raises
    ------
    HTTPException (400)
        If the booking date is in the past or outside the allowed window.
    """

    # Validate the requested date
    validate_booking_date(booking_date)

    # Single LEFT JOIN: seats + active bookings for the given date
    stmt = (
        select(Seat.id, Seat.seat_number, Booking.status)
        .outerjoin(
            Booking,
            (Booking.seat_id == Seat.id)
            & (Booking.booking_date == booking_date)
            & (Booking.status.in_([CONFIRMED, CHECKED_IN])),
        )
        .order_by(Seat.seat_number.asc())
    )

    rows = db.execute(stmt).all()

    return [
        {
            "seat_id": str(row.id),
            "seat_number": row.seat_number,
            "status": row.status if row.status else "available",
        }
        for row in rows
    ]
