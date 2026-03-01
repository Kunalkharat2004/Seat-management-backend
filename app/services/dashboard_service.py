from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.seat import Seat
from app.models.booking import Booking
from app.types.user_types import ROLE_EMPLOYEE, STATUS_ACTIVE, STATUS_INACTIVE
from app.types.booking_status import CONFIRMED, CHECKED_IN

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    async def get_admin_metrics(self) -> dict:
        """
        Fetch aggregated dashboard metrics in a single DB roundtrip.
        Uses scalar subqueries to combine multiple counts into one SELECT statement.
        """
        # Construct scalar subqueries for each metric as requested
        # total_employees: COUNT(*) FROM users WHERE role='employee'
        total_employees_sq = select(func.count(User.id)).where(User.role == ROLE_EMPLOYEE).scalar_subquery()
        
        # active_employees: COUNT(*) FROM users WHERE role='employee' AND status='active'
        active_employees_sq = select(func.count(User.id)).where(
            User.role == ROLE_EMPLOYEE, 
            User.status == STATUS_ACTIVE
        ).scalar_subquery()
        
        # inactive_employees: COUNT(*) FROM users WHERE role='employee' AND status='inactive'
        inactive_employees_sq = select(func.count(User.id)).where(
            User.role == ROLE_EMPLOYEE, 
            User.status == STATUS_INACTIVE
        ).scalar_subquery()
        
        # total_seats: COUNT(*) FROM seats
        total_seats_sq = select(func.count(Seat.id)).scalar_subquery()
        
        # today_bookings: COUNT(*) FROM bookings WHERE booking_date = CURRENT_DATE AND status IN ('confirmed', 'checked_in')
        today_bookings_sq = select(func.count(Booking.id)).where(
            Booking.booking_date == func.current_date(),
            Booking.status.in_([CONFIRMED, CHECKED_IN])
        ).scalar_subquery()
        
        # today_checked_in: COUNT(*) FROM bookings WHERE booking_date = CURRENT_DATE AND status = 'checked_in'
        today_checked_in_sq = select(func.count(Booking.id)).where(
            Booking.booking_date == func.current_date(),
            Booking.status == CHECKED_IN
        ).scalar_subquery()
        
        # today_confirmed: COUNT(*) FROM bookings WHERE booking_date = CURRENT_DATE AND status = 'confirmed'
        today_confirmed_sq = select(func.count(Booking.id)).where(
            Booking.booking_date == func.current_date(),
            Booking.status == CONFIRMED
        ).scalar_subquery()

        # Combine all subqueries into a single SELECT statement for a single DB roundtrip
        stmt = select(
            total_employees_sq.label("total_employees"),
            active_employees_sq.label("active_employees"),
            inactive_employees_sq.label("inactive_employees"),
            total_seats_sq.label("total_seats"),
            today_bookings_sq.label("today_bookings"),
            today_checked_in_sq.label("today_checked_in"),
            today_confirmed_sq.label("today_confirmed")
        )

        result = self.db.execute(stmt).fetchone()

        if not result:
            return {
                "total_employees": 0,
                "active_employees": 0,
                "inactive_employees": 0,
                "total_seats": 0,
                "today_bookings": 0,
                "today_checked_in": 0,
                "today_confirmed": 0,
            }

        return {
            "total_employees": result.total_employees or 0,
            "active_employees": result.active_employees or 0,
            "inactive_employees": result.inactive_employees or 0,
            "total_seats": result.total_seats or 0,
            "today_bookings": result.today_bookings or 0,
            "today_checked_in": result.today_checked_in or 0,
            "today_confirmed": result.today_confirmed or 0,
        }
