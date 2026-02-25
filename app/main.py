from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Import models so Base.metadata knows about all tables
import app.models  # noqa: F401


def create_app() -> FastAPI:
    app = FastAPI(
        title="Seat Management API",
        description="Digital Workspace Seat Management Platform",
        version="0.1.0",
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
    app.include_router(admin_router)
    app.include_router(auth_router)

    return app


app = create_app()
