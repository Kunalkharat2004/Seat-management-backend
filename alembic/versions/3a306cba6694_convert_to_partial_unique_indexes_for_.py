"""convert to partial unique indexes for bookings

Revision ID: 3a306cba6694
Revises: f2a617436f29
Create Date: 2026-02-26 14:35:34.097600

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a306cba6694'
down_revision: Union[str, None] = 'f2a617436f29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Drop existing hard unique constraints ─────────────────────
    op.drop_constraint("uq_employee_booking_date", "bookings", type_="unique")
    op.drop_constraint("uq_seat_booking_date", "bookings", type_="unique")

    # ── Create partial unique indexes ─────────────────────────────
    # Only enforce uniqueness for active bookings (confirmed / checked_in).
    # Cancelled and expired bookings are excluded so a seat/employee can be
    # re-booked on a date where a prior booking was cancelled/expired.
    op.create_index(
        "uq_seat_booking_active",
        "bookings",
        ["seat_id", "booking_date"],
        unique=True,
        postgresql_where=sa.text("status IN ('confirmed', 'checked_in')"),
    )
    op.create_index(
        "uq_employee_booking_active",
        "bookings",
        ["employee_id", "booking_date"],
        unique=True,
        postgresql_where=sa.text("status IN ('confirmed', 'checked_in')"),
    )


def downgrade() -> None:
    # ── Drop partial indexes ──────────────────────────────────────
    op.drop_index("uq_employee_booking_active", table_name="bookings")
    op.drop_index("uq_seat_booking_active", table_name="bookings")

    # ── Recreate original hard unique constraints ─────────────────
    op.create_unique_constraint(
        "uq_employee_booking_date", "bookings", ["employee_id", "booking_date"]
    )
    op.create_unique_constraint(
        "uq_seat_booking_date", "bookings", ["seat_id", "booking_date"]
    )

