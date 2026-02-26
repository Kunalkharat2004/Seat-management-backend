"""
Service layer for booking operations — create, cancel, and check-in.
"""

import logging
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.user import User

logger = logging.getLogger(__name__)


# ── Create Booking ────────────────────────────────────────────────


async def create_booking(
    db: Session,
    current_user: User,
    seat_id: str,
    booking_date: date,
) -> dict:
    """Create a new seat booking for the current user.

    Relies on partial unique indexes in the database to enforce:
      - One active booking per employee per day
      - One active booking per seat per day

    Raises
    ------
    HTTPException (403)
        If the user account is inactive.
    HTTPException (400)
        If the booking date is in the past.
    HTTPException (409)
        If a DB unique-constraint violation occurs (duplicate booking).
    """

    # 1. User must be active
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive users cannot create bookings.",
        )

    # 2. Booking date cannot be in the past
    if booking_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a seat for a past date.",
        )

    # 3. Build the booking row
    booking = Booking(
        employee_id=current_user.id,
        seat_id=seat_id,
        booking_date=booking_date,
        status="confirmed",
    )

    try:
        db.add(booking)
        db.commit()
        db.refresh(booking)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Seat already booked or user already has booking for this date.",
        )

    logger.info(
        "Booking %s created — user=%s seat=%s date=%s",
        booking.id, current_user.employee_id, seat_id, booking_date,
    )

    return {
        "message": "Booking confirmed.",
        "booking_id": str(booking.id),
        "seat_id": str(booking.seat_id),
        "booking_date": str(booking.booking_date),
        "status": booking.status,
    }


# ── Cancel Booking ───────────────────────────────────────────────


async def cancel_booking(
    db: Session,
    booking_id: str,
    current_user: User,
) -> dict:
    """Cancel an existing booking.

    Only the booking owner can cancel, and only while the status is
    ``confirmed``.

    Raises
    ------
    HTTPException (404)
        If the booking does not exist.
    HTTPException (403)
        If the current user is not the booking owner.
    HTTPException (400)
        If the booking is not in ``confirmed`` status.
    """

    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    if booking.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own bookings.",
        )

    if booking.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a booking with status '{booking.status}'.",
        )

    booking.status = "cancelled"
    booking.cancelled_by = "user"
    db.commit()

    logger.info(
        "Booking %s cancelled by user %s.",
        booking_id, current_user.employee_id,
    )

    return {
        "message": "Booking cancelled.",
        "booking_id": str(booking.id),
        "status": booking.status,
    }


# ── Check-in Booking ─────────────────────────────────────────────


async def check_in_booking(
    db: Session,
    booking_id: str,
    current_user: User,
) -> dict:
    """Check in to an existing booking.

    Only the booking owner can check in, and only while the status is
    ``confirmed``.

    Raises
    ------
    HTTPException (404)
        If the booking does not exist.
    HTTPException (403)
        If the current user is not the booking owner.
    HTTPException (400)
        If the booking is not in ``confirmed`` status.
    """

    booking = db.query(Booking).filter(Booking.id == booking_id).first()

    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found.",
        )

    if booking.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only check in to your own bookings.",
        )

    if booking.status != "confirmed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check in to a booking with status '{booking.status}'.",
        )

    booking.status = "checked_in"
    booking.check_in_time = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "Booking %s checked in by user %s.",
        booking_id, current_user.employee_id,
    )

    return {
        "message": "Check-in successful.",
        "booking_id": str(booking.id),
        "status": booking.status,
        "check_in_time": str(booking.check_in_time),
    }
