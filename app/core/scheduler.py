"""
APScheduler configuration — booking expiry job.

Runs every 5 minutes.  The SQL query inside expire_unchecked_bookings()
includes a CURRENT_TIME >= '10:30' guard, so before 10:30 AM the job
is a harmless no-op.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.db.session import SessionLocal
from app.services.expiry_service import expire_unchecked_bookings

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _run_expiry_job() -> None:
    """Wrapper executed by the scheduler in a background thread.

    Opens its own DB session — fully independent of the FastAPI
    request lifecycle.
    """
    db = SessionLocal()
    try:
        count = expire_unchecked_bookings(db)
        logger.info("Scheduled expiry job finished — %d row(s) expired.", count)
    except Exception:
        logger.exception("Scheduled expiry job failed.")
    finally:
        db.close()


def start_scheduler() -> None:
    """Register the interval job and start the scheduler."""
    scheduler.add_job(
        _run_expiry_job,
        trigger="interval",
        minutes=5,
        id="expire_bookings_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Expiry scheduler running every 5 minutes.")


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Booking expiry scheduler shut down.")


