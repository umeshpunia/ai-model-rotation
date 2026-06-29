"""HealthLog entity: outcome of a provider/key health check."""
from __future__ import annotations
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.domain.enums import HealthStatus
from app.domain.entities.base import IDMixin, utcnow
from app.domain.entities.types import enum_column, string_column


class HealthLog(IDMixin, table=True):
    """A single health-check result produced by the background monitor."""

    __tablename__ = "health_logs"

    created_at: datetime = Field(default_factory=utcnow, nullable=False, index=True)

    provider_id: int | None = Field(default=None, foreign_key="providers.id", index=True)
    api_key_id: int | None = Field(default=None, foreign_key="api_keys.id", index=True)

    check_type: str = Field(default="key", sa_column=string_column(40, nullable=False))
    status: HealthStatus = Field(
        default=HealthStatus.UNKNOWN, sa_column=enum_column(HealthStatus, index=True)
    )
    status_code: int | None = Field(default=None)
    latency_ms: float | None = Field(default=None)
    success: bool = Field(default=False, index=True)
    message: str = Field(default="", sa_column=string_column(500, nullable=False))
