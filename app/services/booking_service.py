"""
Service layer for booking operations — create, cancel, and check-in.
"""

import calendar
import logging
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.user import User
from app.types.booking_status import (
    CANCELLED,
    CANCELLED_BY_USER,
    CHECKED_IN,
    CONFIRMED,
)
from app.types.user_types import STATUS_ACTIVE

logger = logging.getLogger(__name__)

_IST = ZoneInfo("Asia/Kolkata")


# ── Date validation ───────────────────────────────────────────────


def validate_booking_date(booking_date: date) -> None:
    """Enforce all business rules for a valid booking date.

    Rules
    -----
    1. Date must not be in the past (relative to today in IST).
    2. Date must fall within the current calendar month, OR
    3. Booking for next month is allowed ONLY on the last calendar day
       of the current month — and only for the 1st of next month.
    4. Far-future dates beyond the allowed window are rejected.

    All comparisons use Asia/Kolkata (IST) as the reference timezone.

    Raises
    ------
    HTTPException (400)
        If any rule is violated.
    """
    today: date = datetime.now(_IST).date()

    # Rule 1 & 5 — reject past dates
    if booking_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a seat for a past date.",
        )

    current_year: int  = today.year
    current_month: int = today.month

    # Last calendar day of the current month (handles leap years + Dec)
    last_day_of_current_month: int = calendar.monthrange(current_year, current_month)[1]
    is_last_day_of_month: bool = (today.day == last_day_of_current_month)

    # First day of next month (handles December -> January transition)
    if current_month == 12:
        next_month_year: int  = current_year + 1
        next_month: int       = 1
    else:
        next_month_year = current_year
        next_month      = current_month + 1

    next_month_first = date(next_month_year, next_month, 1)

    # Rule 2 — booking is within current month: always allowed
    if booking_date.year == current_year and booking_date.month == current_month:
        return

    # Rule 3 & 4 — booking is for next month's 1st day on last day of month
    if is_last_day_of_month and booking_date == next_month_first:
        return

    # Everything else (far future, wrong month, wrong next-month day) is rejected
    if booking_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking not allowed for this date.",
        )


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
    if current_user.status != STATUS_ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive users cannot create bookings.",
        )

    # 2. Validate booking date (IST-aware: past, current month, next-month rules)
    validate_booking_date(booking_date)

    # 3. Build the booking row
    booking = Booking(
        employee_id=current_user.id,
        seat_id=seat_id,
        booking_date=booking_date,
        status=CONFIRMED,
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

    if booking.status != CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel a booking with status '{booking.status}'.",
        )

    booking.status = CANCELLED
    booking.cancelled_by = CANCELLED_BY_USER
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

    if booking.status != CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check in to a booking with status '{booking.status}'.",
        )

    booking.status = CHECKED_IN
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



# ── Date validation ───────────────────────────────────────────────


def validate_booking_date(booking_date: date) -> None:
    """Enforce all business rules for a valid booking date.

    Rules
    -----
    1. Date must not be in the past (relative to today in IST).
    2. Date must fall within the current calendar month, OR
    3. Booking for next month is allowed ONLY on the last calendar day
       of the current month — and only for the 1st of next month.
    4. Far-future dates beyond the allowed window are rejected.

    All comparisons use Asia/Kolkata (IST) as the reference timezone.

    Raises
    ------
    HTTPException (400)
        If any rule is violated.
    """
    today: date = datetime.now(_IST).date()

    # Rule 1 & 5 — reject past dates
    if booking_date < today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot book a seat for a past date.",
        )

    current_year: int  = today.year
    current_month: int = today.month

    # Last calendar day of the current month (handles leap years + Dec)
    last_day_of_current_month: int = calendar.monthrange(current_year, current_month)[1]
    is_last_day_of_month: bool = (today.day == last_day_of_current_month)

    # First day of next month (handles December -> January transition)
    if current_month == 12:
        next_month_year: int  = current_year + 1
        next_month: int       = 1
    else:
        next_month_year = current_year
        next_month      = current_month + 1

    next_month_first = date(next_month_year, next_month, 1)

    # Rule 2 — booking is within current month: always allowed
    if booking_date.year == current_year and booking_date.month == current_month:
        return

    # Rule 3 & 4 — booking is for next month's 1st day on last day of month
    if is_last_day_of_month and booking_date == next_month_first:
        return

    # Everything else (far future, wrong month, wrong next-month day) is rejected
    if booking_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking not allowed for this date.",
        )


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

    # 2. Validate booking date (IST-aware: past, current month, next-month rules)
    validate_booking_date(booking_date)

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
