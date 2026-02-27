"""Seat routes — listing and availability."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.jwt import get_current_user
from app.db.session import get_db
from app.services.seat_service import get_all_seats, get_seat_availability

router = APIRouter(prefix="/seats", tags=["seats"])


@router.get("")
async def list_seats(db: Session = Depends(get_db)):
    """Return all seats ordered by seat number."""
    return await get_all_seats(db)


@router.get("/availability")
async def seat_availability(
    date: date = Query(..., description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
):
    """Return all seats with availability status for a given date."""
    return await get_seat_availability(db, date)
