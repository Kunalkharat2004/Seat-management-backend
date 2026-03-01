"""Pydantic schemas for booking endpoints."""

import uuid
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ── Request schemas ───────────────────────────────────────────────


class CreateBookingRequest(BaseModel):
    """Body for POST /bookings."""

    seat_id: str
    booking_date: date


# ── Booking status enum (for query-param validation) ─────────────


class BookingStatusEnum(str, Enum):
    confirmed = "confirmed"
    checked_in = "checked_in"
    expired = "expired"
    cancelled = "cancelled"


# ── Response schemas for GET /bookings/me ─────────────────────────


class MyBookingResponse(BaseModel):
    """Single booking item returned by GET /bookings/me."""

    id: uuid.UUID
    seat_id: uuid.UUID
    seat_number: str
    booking_date: date
    status: str
    check_in_time: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedMyBookings(BaseModel):
    """Paginated wrapper for GET /bookings/me."""

    items: list[MyBookingResponse]
    total: int
    page: int
    page_size: int
