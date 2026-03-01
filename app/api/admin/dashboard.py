from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_admin_user
from app.services.dashboard_service import DashboardService
from app.models.user import User

router = APIRouter(prefix="/admin/dashboard", tags=["admin-dashboard"])

def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    """Dependency provider for DashboardService."""
    return DashboardService(db)

@router.get("/metrics")
async def get_dashboard_metrics(
    service: DashboardService = Depends(get_dashboard_service),
    _admin: User = Depends(get_current_admin_user),
):
    """
    Get aggregated dashboard metrics. 
    Restricted to admin users only.
    """
    return await service.get_admin_metrics()
