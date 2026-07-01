from fastapi import APIRouter
from app.routers.auth import router as auth_router
from app.routers.providers import router as providers_router
from app.routers.keys import router as keys_router
from app.routers.models import router as models_router
from app.routers.settings import router as settings_router
from app.routers.health import router as health_router
from app.routers.statistics import router as statistics_router
from app.routers.logs import router as logs_router
from app.routers.notifications import router as notifications_router
from app.routers.backups import router as backups_router
from app.routers.gateway import router as gateway_router_impl
from app.routers.agents import router as agents_router

# Admin & Management API router (v1)
api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(providers_router, prefix="/providers", tags=["providers"])
api_router.include_router(keys_router, prefix="/keys", tags=["keys"])
api_router.include_router(models_router, prefix="/models", tags=["models"])
api_router.include_router(settings_router, prefix="/settings", tags=["settings"])
api_router.include_router(health_router, tags=["health"])  # Prefix handled internally (e.g. /health and /status)
api_router.include_router(statistics_router, prefix="/statistics", tags=["statistics"])
api_router.include_router(logs_router, prefix="/logs", tags=["logs"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(backups_router, prefix="/backups", tags=["backups"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])

# Completions Proxy Gateway Router (v1)
gateway_router = APIRouter()
gateway_router.include_router(gateway_router_impl)

# Export routes
__all__ = ["api_router", "gateway_router"]
