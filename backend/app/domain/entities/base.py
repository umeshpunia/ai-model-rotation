"""Base entity primitives and shared mixins for all domain models."""
from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import func
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class TimestampMixin(SQLModel):
    """Mixin providing auto-managed created_at / updated_at columns."""

    created_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": func.now()},
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": utcnow,
        },
    )


class IDMixin(SQLModel):
    """Mixin providing an auto-increment integer primary key."""

    id: int | None = Field(default=None, primary_key=True)
