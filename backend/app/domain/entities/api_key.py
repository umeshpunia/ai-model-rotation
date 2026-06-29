"""ApiKey entity: an encrypted provider credential with health/usage state."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.domain.enums import HealthStatus, KeyStatus
from app.domain.entities.base import IDMixin, TimestampMixin
from app.domain.entities.types import enum_column, string_column

if TYPE_CHECKING:
    from app.domain.entities.provider import Provider


class ApiKey(IDMixin, TimestampMixin, table=True):
    """A single provider API key.

    The secret itself is never stored in plaintext: ``encrypted_key`` holds an
    AES-256-GCM blob (nonce + ciphertext), and ``key_hint`` keeps a masked
    fragment for display. Rotation, cooldown, and health state all live here so
    the routing engine can pick a usable key without touching the secret.
    """

    __tablename__ = "api_keys"

    provider_id: int = Field(foreign_key="providers.id", index=True, nullable=False)

    name: str = Field(sa_column=string_column(120, nullable=False))
    # Encrypted secret material (base64 nonce + ciphertext json-encoded).
    encrypted_key: str = Field(sa_column=string_column(2048, nullable=False))
    key_hint: str = Field(default="", sa_column=string_column(64, nullable=False))
    fingerprint: str = Field(
        default="", sa_column=string_column(64, nullable=False, index=True)
    )

    # Lifecycle / routing
    status: KeyStatus = Field(
        default=KeyStatus.UNKNOWN, sa_column=enum_column(KeyStatus, index=True)
    )
    health_status: HealthStatus = Field(
        default=HealthStatus.UNKNOWN, sa_column=enum_column(HealthStatus, index=True)
    )
    is_enabled: bool = Field(default=True, index=True)
    priority: int = Field(default=100, index=True)

    # Usage statistics
    usage_count: int = Field(default=0)
    success_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    consecutive_failures: int = Field(default=0)
    total_tokens: int = Field(default=0)
    total_cost: float = Field(default=0.0)

    # Latency tracking (milliseconds)
    last_latency_ms: float | None = Field(default=None)
    avg_latency_ms: float | None = Field(default=None)

    # Timing / recovery
    last_used_at: datetime | None = Field(default=None)
    last_success_at: datetime | None = Field(default=None)
    last_failure_at: datetime | None = Field(default=None)
    cooldown_until: datetime | None = Field(default=None, index=True)
    expires_at: datetime | None = Field(default=None)

    # Diagnostics
    last_status_code: int | None = Field(default=None)
    last_error: str = Field(default="", sa_column=string_column(500, nullable=False))

    # Relationships
    provider: "Provider" = Relationship(back_populates="api_keys")
