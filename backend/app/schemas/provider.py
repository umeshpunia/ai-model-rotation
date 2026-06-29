"""Provider request/response DTOs."""
from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.domain.enums import ApiFormat, AuthType, ProviderStatus
from app.schemas.common import ORMSchema, SchemaBase


def _slugify(value: str) -> str:
    """Normalise a string into a lowercase, dash-separated slug."""
    cleaned = "".join(c if c.isalnum() else "-" for c in value.strip().lower())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-")


class ProviderBase(SchemaBase):
    """Fields shared by provider create/update."""

    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    plugin: str = Field(min_length=1, max_length=80, description="Plugin identifier.")
    api_format: ApiFormat = ApiFormat.OPENAI
    auth_type: AuthType = AuthType.BEARER
    base_url: str = Field(min_length=1, max_length=500)
    default_model: str = Field(default="", max_length=200)
    priority: int = Field(default=100, ge=0)
    timeout_seconds: int | None = Field(default=None, ge=1)
    max_retries: int | None = Field(default=None, ge=0)
    config: dict[str, Any] = Field(default_factory=dict)
    extra_headers: dict[str, Any] = Field(default_factory=dict)


class ProviderCreate(ProviderBase):
    """Payload for creating a provider."""

    slug: str | None = Field(default=None, max_length=80)
    is_enabled: bool = True
    status: ProviderStatus = ProviderStatus.ENABLED

    @field_validator("slug")
    @classmethod
    def _normalise_slug(cls, v: str | None) -> str | None:
        return _slugify(v) if v else v


class ProviderUpdate(SchemaBase):
    """Partial update payload for a provider (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    plugin: str | None = Field(default=None, min_length=1, max_length=80)
    api_format: ApiFormat | None = None
    auth_type: AuthType | None = None
    base_url: str | None = Field(default=None, min_length=1, max_length=500)
    default_model: str | None = Field(default=None, max_length=200)
    priority: int | None = Field(default=None, ge=0)
    status: ProviderStatus | None = None
    is_enabled: bool | None = None
    timeout_seconds: int | None = Field(default=None, ge=1)
    max_retries: int | None = Field(default=None, ge=0)
    config: dict[str, Any] | None = None
    extra_headers: dict[str, Any] | None = None


class ProviderRead(ORMSchema):
    """Provider as returned by the API."""

    id: int
    name: str
    slug: str
    description: str
    plugin: str
    api_format: ApiFormat
    auth_type: AuthType
    base_url: str
    default_model: str
    status: ProviderStatus
    is_enabled: bool
    priority: int
    timeout_seconds: int | None
    max_retries: int | None
    config: dict[str, Any]
    extra_headers: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class ProviderTestResult(ORMSchema):
    """Outcome of a provider connection test."""

    provider_id: int
    success: bool
    latency_ms: float | None = None
    status_code: int | None = None
    message: str = ""
