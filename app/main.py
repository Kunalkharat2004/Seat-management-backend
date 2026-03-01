from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.scheduler import shutdown_scheduler, start_scheduler

# Import models so Base.metadata knows about all tables
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the application."""
    start_scheduler()
    yield
    shutdown_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Seat Management API",
        description="Digital Workspace Seat Management Platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health check ──────────────────────────────────────────────
    @app.get("/health", tags=["health"])
    def health_check():
        return {"status": "ok"}

    # ── Routers ───────────────────────────────────────────────────
    from app.routes.admin import router as admin_router
    from app.routes.auth import router as auth_router
    from app.routes.bookings import router as bookings_router
    from app.routes.seat_admin import router as seat_admin_router
    from app.routes.seats import router as seats_router
    from app.api.admin.dashboard import router as dashboard_router
    app.include_router(admin_router)
    app.include_router(auth_router)
    app.include_router(bookings_router)
    app.include_router(seat_admin_router)
    app.include_router(seats_router)
    app.include_router(dashboard_router)

    return app


app = create_app()

