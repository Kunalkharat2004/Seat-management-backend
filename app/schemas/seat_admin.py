"""Pydantic schemas for admin seat-management endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SeatCreateRequest(BaseModel):
    """Body for POST /admin/seats."""

    seat_number: str


class SeatUpdateRequest(BaseModel):
    """Body for PATCH /admin/seats/{seat_id}."""

    seat_number: str | None = None


class SeatResponse(BaseModel):
    """Public seat representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    seat_number: str
    created_at: datetime


class BulkSeatUploadResponse(BaseModel):
    """Response for POST /admin/seats/bulk-upload."""

    total_rows: int
    successful_creations: int
    skipped_rows: int
    failed_rows: int


class PaginatedSeatResponse(BaseModel):
    """Paginated list of seats."""

    total: int
    page: int
    page_size: int
    items: list[SeatResponse]
