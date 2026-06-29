"""Setting entity: a persisted key/value application setting."""
from __future__ import annotations
from typing import Any

from sqlmodel import Field, SQLModel

from app.domain.entities.base import IDMixin, TimestampMixin
from app.domain.entities.types import json_column, string_column


class Setting(IDMixin, TimestampMixin, table=True):
    """A single persisted setting.

    Values are stored as JSON so any scalar/structure can round-trip. The
    ``group`` field organises settings for the UI (e.g. routing, notifications),
    and ``is_secret`` marks values that must be masked in API responses.
    """

    __tablename__ = "settings"

    key: str = Field(sa_column=string_column(150, nullable=False, unique=True, index=True))
    value: Any = Field(default=None, sa_column=json_column(nullable=True))
    value_type: str = Field(default="string", sa_column=string_column(20, nullable=False))
    group: str = Field(default="general", sa_column=string_column(60, nullable=False, index=True))
    description: str = Field(default="", sa_column=string_column(500, nullable=False))
    is_secret: bool = Field(default=False)
    is_editable: bool = Field(default=True)
    profile: str = Field(default="default", sa_column=string_column(40, nullable=False, index=True))
