"""Booking routes — create, cancel, and check-in."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.jwt import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.booking import CreateBookingRequest
from app.services.booking_service import (
    cancel_booking,
    check_in_booking,
    create_booking,
)
from app.helpers.bookings import _resolve_user

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_booking_route(
    body: CreateBookingRequest,
    db: Session = Depends(get_db),
    employee_id: str = Depends(get_current_user),
):
    """Book a seat for a given date."""
    current_user = _resolve_user(db, employee_id)
    return await create_booking(db, current_user, body.seat_id, body.booking_date)


@router.post("/{booking_id}/cancel")
async def cancel_booking_route(
    booking_id: str,
    db: Session = Depends(get_db),
    employee_id: str = Depends(get_current_user),
):
    """Cancel an existing booking."""
    current_user = _resolve_user(db, employee_id)
    return await cancel_booking(db, booking_id, current_user)


@router.post("/{booking_id}/check-in")
async def check_in_booking_route(
    booking_id: str,
    db: Session = Depends(get_db),
    employee_id: str = Depends(get_current_user),
):
    """Check in to an existing booking."""
    current_user = _resolve_user(db, employee_id)
    return await check_in_booking(db, booking_id, current_user)
