"""Settings request/response DTOs and import/export envelopes."""
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import ORMSchema, SchemaBase


class SettingUpsert(SchemaBase):
    """Payload for creating or updating a single setting."""

    key: str = Field(min_length=1, max_length=150)
    value: Any = None
    value_type: str = Field(default="string", max_length=20)
    group: str = Field(default="general", max_length=60)
    description: str = Field(default="", max_length=500)
    is_secret: bool = False
    profile: str = Field(default="default", max_length=40)


class SettingRead(ORMSchema):
    """A setting as returned by the API (secret values are masked upstream)."""

    id: int
    key: str
    value: Any
    value_type: str
    group: str
    description: str
    is_secret: bool
    is_editable: bool
    profile: str
    created_at: datetime
    updated_at: datetime


class SettingsBulkUpdate(SchemaBase):
    """Payload for updating multiple settings at once."""

    profile: str = Field(default="default", max_length=40)
    values: dict[str, Any] = Field(description="Map of setting key to value.")


class SettingsExport(ORMSchema):
    """Exported settings snapshot for backup / transfer."""

    profile: str
    exported_at: datetime
    settings: list[SettingRead]


class SettingsImport(SchemaBase):
    """Import payload accepting a settings snapshot."""

    profile: str = Field(default="default", max_length=40)
    overwrite: bool = Field(default=True, description="Overwrite existing keys.")
    settings: list[SettingUpsert]
