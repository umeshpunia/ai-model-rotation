"""Request log and health log response DTOs."""
from datetime import datetime

from app.domain.enums import HealthStatus
from app.schemas.common import ORMSchema


class RequestLogRead(ORMSchema):
    """A single request log entry."""

    id: int
    created_at: datetime
    provider_id: int | None
    api_key_id: int | None
    model: str
    task_type: str
    endpoint: str
    method: str
    success: bool
    status_code: int | None
    latency_ms: float | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    retries: int
    fallback_used: bool
    error_code: str
    error_message: str
    request_id: str
    client_ip: str


class HealthLogRead(ORMSchema):
    """A single health-check log entry."""

    id: int
    created_at: datetime
    provider_id: int | None
    api_key_id: int | None
    check_type: str
    status: HealthStatus
    status_code: int | None
    latency_ms: float | None
    success: bool
    message: str
