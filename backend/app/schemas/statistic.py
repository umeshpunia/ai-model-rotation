"""Statistics and dashboard response DTOs."""
from datetime import datetime

from app.domain.enums import StatisticWindow
from app.schemas.common import ORMSchema


class StatisticRead(ORMSchema):
    """A single aggregated statistics bucket."""

    id: int
    window: StatisticWindow
    bucket: datetime
    provider_id: int | None
    api_key_id: int | None
    model: str
    request_count: int
    success_count: int
    failure_count: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost: float
    avg_latency_ms: float
    max_latency_ms: float


class DashboardStats(ORMSchema):
    """Aggregated snapshot powering the live dashboard."""

    active_provider: str | None = None
    active_model: str | None = None
    current_key_hint: str | None = None
    total_providers: int = 0
    total_keys: int = 0
    healthy_keys: int = 0
    disabled_keys: int = 0
    requests_today: int = 0
    tokens_used: int = 0
    average_latency_ms: float = 0.0
    total_cost: float = 0.0
    success_rate: float = 0.0
    unread_notifications: int = 0
