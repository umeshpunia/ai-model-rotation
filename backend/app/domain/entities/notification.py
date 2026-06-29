"""Notification entity: an alert raised by the system and its delivery state."""
from __future__ import annotations
from datetime import datetime
from typing import Any

from sqlmodel import Field, SQLModel

from app.domain.enums import NotificationChannel, NotificationSeverity
from app.domain.entities.base import IDMixin, utcnow
from app.domain.entities.types import enum_column, json_column, string_column


class Notification(IDMixin, table=True):
    """A persisted notification / alert.

    Records both the human-facing message and the delivery outcome across one
    or more channels (desktop, email, Slack, ...). The notification-cleanup job
    prunes old, read, and successfully-sent rows.
    """

    __tablename__ = "notifications"

    created_at: datetime = Field(default_factory=utcnow, nullable=False, index=True)

    channel: NotificationChannel = Field(
        default=NotificationChannel.DESKTOP, sa_column=enum_column(NotificationChannel, index=True)
    )
    severity: NotificationSeverity = Field(
        default=NotificationSeverity.INFO, sa_column=enum_column(NotificationSeverity, index=True)
    )
    event_type: str = Field(default="", sa_column=string_column(80, nullable=False, index=True))
    title: str = Field(sa_column=string_column(200, nullable=False))
    message: str = Field(default="", sa_column=string_column(2000, nullable=False))

    is_read: bool = Field(default=False, index=True)
    is_sent: bool = Field(default=False, index=True)
    sent_at: datetime | None = Field(default=None)
    delivery_error: str = Field(default="", sa_column=string_column(500, nullable=False))

    meta: dict[str, Any] = Field(default_factory=dict, sa_column=json_column())
