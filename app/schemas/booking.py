"""Pydantic schemas for booking endpoints."""

from datetime import date

from pydantic import BaseModel


class CreateBookingRequest(BaseModel):
    """Body for POST /bookings."""

    seat_id: str
    booking_date: date
