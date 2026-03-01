"""Booking routes — create, cancel, check-in, and list my bookings."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.jwt import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.booking import (
    BookingStatusEnum,
    CreateBookingRequest,
    PaginatedMyBookings,
)
from app.services.booking_service import (
    cancel_booking,
    check_in_booking,
    create_booking,
    get_my_bookings,
)
from app.helpers.bookings import _resolve_user

router = APIRouter(prefix="/bookings", tags=["bookings"])


# ── GET /bookings/me  (must be BEFORE /{booking_id} routes) ──────


@router.get("/me", response_model=PaginatedMyBookings)
async def get_my_bookings_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[BookingStatusEnum] = Query(None),
    date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    employee_id: str = Depends(get_current_user),
):
    """Return the authenticated user's bookings (paginated)."""
    current_user = _resolve_user(db, employee_id)
    return await get_my_bookings(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status.value if status else None,
        date_filter=date,
    )


# ── POST /bookings ───────────────────────────────────────────────


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_booking_route(
    body: CreateBookingRequest,
    db: Session = Depends(get_db),
    employee_id: str = Depends(get_current_user),
):
    """Book a seat for a given date."""
    current_user = _resolve_user(db, employee_id)
    return await create_booking(db, current_user, body.seat_id, body.booking_date)


# ── POST /bookings/{booking_id}/cancel ───────────────────────────


@router.post("/{booking_id}/cancel")
async def cancel_booking_route(
    booking_id: str,
    db: Session = Depends(get_db),
    employee_id: str = Depends(get_current_user),
):
    """Cancel an existing booking."""
    current_user = _resolve_user(db, employee_id)
    return await cancel_booking(db, booking_id, current_user)


# ── POST /bookings/{booking_id}/check-in ─────────────────────────


@router.post("/{booking_id}/check-in")
async def check_in_booking_route(
    booking_id: str,
    db: Session = Depends(get_db),
    employee_id: str = Depends(get_current_user),
):
    """Check in to an existing booking."""
    current_user = _resolve_user(db, employee_id)
    return await check_in_booking(db, booking_id, current_user)
