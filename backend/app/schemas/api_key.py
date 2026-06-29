"""API key request/response DTOs. Secrets are never returned in read models."""
from datetime import datetime

from pydantic import Field

from app.domain.enums import HealthStatus, KeyStatus
from app.schemas.common import ORMSchema, SchemaBase


class ApiKeyCreate(SchemaBase):
    """Payload for adding a new API key (plaintext secret accepted once)."""

    provider_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=120)
    key: str = Field(min_length=1, max_length=2048, description="Plaintext API key (encrypted at rest).")
    priority: int = Field(default=100, ge=0)
    is_enabled: bool = True
    expires_at: datetime | None = None


class ApiKeyUpdate(SchemaBase):
    """Partial update payload for an API key."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    key: str | None = Field(default=None, min_length=1, max_length=2048, description="Replacement secret.")
    priority: int | None = Field(default=None, ge=0)
    is_enabled: bool | None = None
    status: KeyStatus | None = None
    expires_at: datetime | None = None


class ApiKeyRead(ORMSchema):
    """API key as returned by the API — only a masked hint is exposed."""

    id: int
    provider_id: int
    name: str
    key_hint: str
    status: KeyStatus
    health_status: HealthStatus
    is_enabled: bool
    priority: int
    usage_count: int
    success_count: int
    failure_count: int
    consecutive_failures: int
    total_tokens: int
    total_cost: float
    last_latency_ms: float | None
    avg_latency_ms: float | None
    last_used_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None
    cooldown_until: datetime | None
    expires_at: datetime | None
    last_status_code: int | None
    last_error: str
    created_at: datetime
    updated_at: datetime


class ApiKeyReveal(ORMSchema):
    """Decrypted secret response — returned only on an explicit reveal action."""

    id: int
    provider_id: int
    name: str
    key: str = Field(description="Decrypted plaintext secret.")


class ApiKeyTestResult(ORMSchema):
    """Outcome of a live API key validation."""

    api_key_id: int
    success: bool
    status: KeyStatus
    latency_ms: float | None = None
    status_code: int | None = None
    message: str = ""
