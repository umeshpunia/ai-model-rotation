"""RequestLog entity: one row per gateway request for auditing and statistics."""
from __future__ import annotations
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel

from app.domain.entities.base import IDMixin
from app.domain.entities.base import utcnow
from app.domain.entities.types import string_column


class RequestLog(IDMixin, table=True):
    """Structured record of a single gateway request.

    Captures provider/key selection, outcome, latency, token usage, cost, and
    failover/retry behaviour so the dashboard and statistics jobs can aggregate
    it. Append-only — cleaned up by the log-cleanup background job.
    """

    __tablename__ = "request_logs"

    created_at: datetime = Field(default_factory=utcnow, nullable=False, index=True)

    # Selection (nullable: a request may fail before any key is chosen)
    provider_id: int | None = Field(default=None, foreign_key="providers.id", index=True)
    api_key_id: int | None = Field(default=None, foreign_key="api_keys.id", index=True)

    model: str = Field(default="", sa_column=string_column(200, nullable=False, index=True))
    task_type: str = Field(default="", sa_column=string_column(40, nullable=False))
    endpoint: str = Field(default="", sa_column=string_column(120, nullable=False))
    method: str = Field(default="POST", sa_column=string_column(10, nullable=False))

    # Outcome
    success: bool = Field(default=False, index=True)
    status_code: int | None = Field(default=None, index=True)
    latency_ms: float | None = Field(default=None)

    # Token usage / cost
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    cost: float = Field(default=0.0)

    # Resilience behaviour
    retries: int = Field(default=0)
    fallback_used: bool = Field(default=False)

    # Error diagnostics
    error_code: str = Field(default="", sa_column=string_column(80, nullable=False))
    error_message: str = Field(default="", sa_column=string_column(1000, nullable=False))

    # Caller context
    request_id: str = Field(default="", sa_column=string_column(64, nullable=False, index=True))
    client_ip: str = Field(default="", sa_column=string_column(64, nullable=False))
