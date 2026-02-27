"""Admin routes — seat CRUD and bulk upload."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.seat_admin import (
    BulkSeatUploadResponse,
    PaginatedSeatResponse,
    SeatCreateRequest,
    SeatResponse,
    SeatUpdateRequest,
)
from app.services.seat_admin_service import (
    bulk_create_seats_from_csv,
    create_seat,
    delete_seat,
    get_seat_by_id,
    get_seats,
    update_seat,
)

router = APIRouter(prefix="/admin", tags=["admin-seats"])


# ── Create ────────────────────────────────────────────────────────


@router.post("/seats", status_code=201, response_model=SeatResponse)
async def create_seat_route(
    body: SeatCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Create a new seat."""
    return await create_seat(db, body)


@router.post("/seats/bulk-upload", status_code=200, response_model=BulkSeatUploadResponse)
async def bulk_upload_seats(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Bulk-create seats from a CSV file.

    Expected CSV column: ``seat_number``
    """
    if file.content_type not in ("text/csv", "application/vnd.ms-excel") and not (
        file.filename or ""
    ).lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a CSV.",
        )

    return await bulk_create_seats_from_csv(db, file)


# ── Read ──────────────────────────────────────────────────────────


@router.get("/seats", response_model=PaginatedSeatResponse)
async def list_seats(
    search: str | None = Query(None, description="Search by seat_number"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Return a paginated list of seats."""
    return await get_seats(db, page, page_size, search)


@router.get("/seats/{seat_id}", response_model=SeatResponse)
async def get_seat_route(
    seat_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Return a single seat by ID."""
    return await get_seat_by_id(db, seat_id)


# ── Update ────────────────────────────────────────────────────────


@router.patch("/seats/{seat_id}", response_model=SeatResponse)
async def update_seat_route(
    seat_id: str,
    body: SeatUpdateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Update a seat's fields."""
    return await update_seat(db, seat_id, body)


# ── Delete (hard) ─────────────────────────────────────────────────


@router.delete("/seats/{seat_id}")
async def delete_seat_route(
    seat_id: str,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin_user),
):
    """Hard-delete a seat."""
    return await delete_seat(db, seat_id)
