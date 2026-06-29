"""Statistic entity: aggregated usage metrics bucketed by time window."""
from __future__ import annotations
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.domain.enums import StatisticWindow
from app.domain.entities.base import IDMixin, TimestampMixin
from app.domain.entities.types import enum_column, string_column


class Statistic(IDMixin, TimestampMixin, table=True):
    """Pre-aggregated metrics for a (window, bucket, provider, key) tuple.

    Produced by the statistics-aggregation background job from RequestLog rows
    so the dashboard can render trends without scanning the raw log table.
    A null ``provider_id``/``api_key_id`` denotes a global (all-up) aggregate.
    """

    __tablename__ = "statistics"

    window: StatisticWindow = Field(
        default=StatisticWindow.DAY, sa_column=enum_column(StatisticWindow, index=True)
    )
    # Start of the time bucket this row aggregates.
    bucket: datetime = Field(nullable=False, index=True)

    provider_id: int | None = Field(default=None, foreign_key="providers.id", index=True)
    api_key_id: int | None = Field(default=None, foreign_key="api_keys.id", index=True)
    model: str = Field(default="", sa_column=string_column(200, nullable=False))

    request_count: int = Field(default=0)
    success_count: int = Field(default=0)
    failure_count: int = Field(default=0)
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)
    total_tokens: int = Field(default=0)
    total_cost: float = Field(default=0.0)
    avg_latency_ms: float = Field(default=0.0)
    max_latency_ms: float = Field(default=0.0)
