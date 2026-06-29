"""Domain enums. Kept in one place for repository/UI reuse."""
from __future__ import annotations
from enum import Enum, StrEnum


class HealthStatus(str, Enum):
    """Provider/key health state used by the scheduler."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class KeyStatus(str, Enum):
    """API key lifecycle status."""
    HEALTHY = "healthy"
    COOLDOWN = "cooldown"
    DISABLED = "disabled"
    INVALID = "invalid"
    EXPIRED = "expired"
    QUOTA_REACHED = "quota_reached"
    UNKNOWN = "unknown"


class ProviderStatus(str, Enum):
    """Provider availability status."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class RoutingMode(str, Enum):
    """Routing strategy for choosing a provider/key."""
    ROUND_ROBIN = "round_robin"
    PRIORITY = "priority"
    LEAST_USED = "least_used"
    FASTEST = "fastest"
    LOWEST_COST = "lowest_cost"
    HIGHEST_SUCCESS = "highest_success"
    RANDOM = "random"
    AI_OPTIMIZED = "ai_optimized"


class TaskType(str, Enum):
    """Logical task category used for per-task routing."""
    GENERAL = "general"
    CODING = "coding"
    REASONING = "reasoning"
    CHEAP = "cheap"
    VISION = "vision"
    IMAGE = "image"
    EMBEDDING = "embedding"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    DESKTOP = "desktop"
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


class NotificationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BackupType(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    PRE_UPDATE = "pre_update"


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class StatisticWindow(str, Enum):
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class ApiFormat(str, Enum):
    """Format used by a provider's API (driven by plugin metadata)."""
    OPENAI = "openai"            # OpenAI-compatible chat completions
    ANTHROPIC = "anthropic"      # Anthropic messages API
    GEMINI = "gemini"            # Google generateContent
    OLLAMA = "ollama"            # Ollama native
    AZURE_OPENAI = "azure_openai"
    CUSTOM = "custom"


class AuthType(str, Enum):
    """API key authentication scheme used by a provider."""
    BEARER = "bearer"
    QUERY_PARAM = "query_param"
    HEADER = "header"
    OAUTH = "oauth"
    NONE = "none"