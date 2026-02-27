"""
Service for expiring unchecked-in bookings.

Called every 5 minutes by the scheduler.  PostgreSQL's CURRENT_TIME
decides whether expiry should actually happen (>= 10:30 AM).
"""

import logging
from datetime import date

from sqlalchemy import text, update
from sqlalchemy.orm import Session

from app.models.booking import Booking
from app.types.booking_status import CONFIRMED, EXPIRED

logger = logging.getLogger(__name__)


def expire_unchecked_bookings(db: Session) -> int:
    """Expire all confirmed bookings for today that were never checked in.

    The query includes ``CURRENT_TIME >= '10:30'`` so that even if the
    scheduler fires before 10:30 AM, **zero rows** are touched.
    This makes the job fully idempotent and restart-safe.

    Returns the number of rows affected.
    """

    today = date.today()

    stmt = (
        update(Booking)
        .where(
            Booking.booking_date == today,
            Booking.status == CONFIRMED,
            Booking.check_in_time.is_(None),
            text("CURRENT_TIME >= '10:30'"),
        )
        .values(status=EXPIRED)
    )

    result = db.execute(stmt)
    db.commit()

    count = result.rowcount
    logger.info(
        "Expiry job complete for %s — %d booking(s) expired.", today, count
    )
    return count

