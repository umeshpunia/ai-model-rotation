"""Application-wide constants."""
from __future__ import annotations
from typing import Final

APP_NAME: Final[str] = "AI Gateway Pro"
APP_VERSION: Final[str] = "1.0.0"
API_TITLE: Final[str] = "AI Gateway Pro REST API"
API_DESCRIPTION: Final[str] = (
    "Production-grade local AI Gateway for managing providers, API keys, "
    "routing, monitoring, and failover."
)
HEALTH_HEALTHY: Final[str] = "healthy"
HEALTH_DEGRADED: Final[str] = "degraded"
HEALTH_UNHEALTHY: Final[str] = "unhealthy"
HEALTH_OFFLINE: Final[str] = "offline"
HEALTH_UNKNOWN: Final[str] = "unknown"
ROLE_ADMIN: Final[str] = "admin"
ROLE_USER: Final[str] = "user"
ROLE_VIEWER: Final[str] = "viewer"
LOG_CHANNEL_APP: Final[str] = "app"
LOG_CHANNEL_GATEWAY: Final[str] = "gateway"
LOG_CHANNEL_REQUEST: Final[str] = "request"
LOG_CHANNEL_HEALTH: Final[str] = "health"
LOG_CHANNEL_PROVIDER: Final[str] = "provider"
MASKED_VALUE: Final[str] = "********"
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 200
