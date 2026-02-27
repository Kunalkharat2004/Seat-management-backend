"""
Service layer for admin seat operations — CRUD and bulk CSV upload.
"""

import csv
import io
import logging

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.models.seat import Seat
from app.schemas.seat_admin import (
    PaginatedSeatResponse,
    SeatCreateRequest,
    SeatResponse,
    SeatUpdateRequest,
)

logger = logging.getLogger(__name__)

_REQUIRED_CSV_COLUMNS = {"seat_number"}


# ── Create ────────────────────────────────────────────────────────


async def create_seat(
    db: Session,
    seat_data: SeatCreateRequest,
) -> SeatResponse:
    """Create a new seat.

    Raises
    ------
    HTTPException (400)
        If ``seat_number`` is empty or blank.
    HTTPException (409)
        If ``seat_number`` already exists.
    """

    seat_number = (seat_data.seat_number or "").strip()

    if not seat_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="seat_number must not be empty.",
        )

    # Uniqueness check
    if db.query(Seat).filter(Seat.seat_number == seat_number).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seat number '{seat_number}' already exists.",
        )

    seat = Seat(seat_number=seat_number)
    db.add(seat)
    db.commit()
    db.refresh(seat)

    logger.info("Seat '%s' created.", seat_number)

    return SeatResponse.model_validate(seat)


# ── Bulk create from CSV ──────────────────────────────────────────


async def bulk_create_seats_from_csv(
    db: Session,
    file: UploadFile,
) -> dict:
    """Parse a CSV file and create seat records row-by-row.

    Each row is processed individually so that a single failure never
    rolls back the entire batch.
    """

    # ── Read & parse CSV ──────────────────────────────────────────
    raw_bytes = await file.read()
    try:
        text = raw_bytes.decode("utf-8-sig")  # handles optional BOM
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not valid UTF-8.",
        )

    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None or not _REQUIRED_CSV_COLUMNS.issubset(
        {col.strip().lower() for col in reader.fieldnames}
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"CSV must contain columns: {', '.join(sorted(_REQUIRED_CSV_COLUMNS))}. "
                f"Found: {reader.fieldnames}"
            ),
        )

    # ── Process rows ──────────────────────────────────────────────
    total = 0
    created = 0
    skipped = 0
    failed = 0

    for row in reader:
        seat_number = (row.get("seat_number") or "").strip()

        if not seat_number:
            # Blank row — ignore silently
            continue

        total += 1

        # Skip duplicates
        if db.query(Seat).filter(Seat.seat_number == seat_number).first():
            logger.info("Row %d: seat_number '%s' already exists, skipping.", total, seat_number)
            skipped += 1
            continue

        try:
            seat = Seat(seat_number=seat_number)
            db.add(seat)
            db.commit()
            db.refresh(seat)
            created += 1
            logger.info("Row %d: seat '%s' created.", total, seat_number)
        except Exception:
            db.rollback()
            failed += 1
            logger.exception("Row %d: failed to create seat '%s'.", total, seat_number)

    return {
        "total_rows": total,
        "successful_creations": created,
        "skipped_rows": skipped,
        "failed_rows": failed,
    }


# ── Read (list + single) ─────────────────────────────────────────


async def get_seats(
    db: Session,
    page: int = 1,
    page_size: int = 10,
    search: str | None = None,
) -> PaginatedSeatResponse:
    """Return a paginated list of seats, optionally filtered by search."""

    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    if page_size > 100:
        page_size = 100

    query = db.query(Seat)

    if search:
        pattern = f"%{search}%"
        query = query.filter(Seat.seat_number.ilike(pattern))

    total = query.count()
    offset = (page - 1) * page_size

    seats = (
        query
        .order_by(Seat.seat_number.asc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return PaginatedSeatResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[SeatResponse.model_validate(s) for s in seats],
    )


async def get_seat_by_id(
    db: Session,
    seat_id: str,
) -> SeatResponse:
    """Fetch a single seat by its UUID.

    Raises
    ------
    HTTPException (404)
        If no seat exists with the given id.
    """

    seat = db.query(Seat).filter(Seat.id == seat_id).first()

    if seat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seat '{seat_id}' not found.",
        )

    return SeatResponse.model_validate(seat)


# ── Update ────────────────────────────────────────────────────────


async def update_seat(
    db: Session,
    seat_id: str,
    update_data: SeatUpdateRequest,
) -> SeatResponse:
    """Update a seat's fields.

    Raises
    ------
    HTTPException (404)
        If no seat exists with the given id.
    HTTPException (409)
        If the new ``seat_number`` already belongs to another seat.
    """

    seat = db.query(Seat).filter(Seat.id == seat_id).first()

    if seat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seat '{seat_id}' not found.",
        )

    update_fields = update_data.model_dump(exclude_unset=True)

    if "seat_number" in update_fields:
        new_number = (update_fields["seat_number"] or "").strip()

        if not new_number:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="seat_number must not be empty.",
            )

        # Uniqueness check (exclude self)
        existing = (
            db.query(Seat)
            .filter(Seat.seat_number == new_number, Seat.id != seat.id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Seat number '{new_number}' already exists.",
            )

        seat.seat_number = new_number

    db.commit()
    db.refresh(seat)

    logger.info("Seat '%s' updated.", seat_id)

    return SeatResponse.model_validate(seat)


# ── Delete (hard) ─────────────────────────────────────────────────


async def delete_seat(
    db: Session,
    seat_id: str,
) -> dict:
    """Hard-delete a seat.

    Raises
    ------
    HTTPException (404)
        If no seat exists with the given id.
    """

    seat = db.query(Seat).filter(Seat.id == seat_id).first()

    if seat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Seat '{seat_id}' not found.",
        )

    # Check for associated bookings
    has_bookings = db.query(Booking).filter(Booking.seat_id == seat.id).first() is not None
    if has_bookings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete seat '{seat.seat_number}' because it has associated bookings. Delete or move the bookings first.",
        )

    db.delete(seat)
    db.commit()

    logger.info("Seat '%s' deleted.", seat_id)

    return {
        "message": f"Seat '{seat_id}' has been deleted.",
        "seat_id": str(seat_id),
    }
