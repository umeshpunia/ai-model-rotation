"""Provider entity: a configured AI provider (Gemini, OpenAI, Anthropic, ...)."""
from typing import TYPE_CHECKING, Any

from sqlmodel import Field, Relationship, SQLModel

from app.domain.enums import ApiFormat, AuthType, ProviderStatus
from app.domain.entities.base import IDMixin, TimestampMixin
from app.domain.entities.types import enum_column, json_column, string_column

if TYPE_CHECKING:
    from app.domain.entities.api_key import ApiKey
    from app.domain.entities.model import Model


class Provider(IDMixin, TimestampMixin, table=True):
    """A configured AI provider. Behaves like a plugin instance.

    Core gateway logic never hardcodes providers — everything (base URL,
    API format, auth scheme, default model) is stored here and resolved
    dynamically by the routing engine and provider plugins.
    """

    __tablename__ = "providers"

    name: str = Field(sa_column=string_column(120, nullable=False))
    slug: str = Field(sa_column=string_column(80, nullable=False, unique=True, index=True))
    description: str = Field(default="", sa_column=string_column(500, nullable=False))

    # Plugin / transport configuration
    plugin: str = Field(sa_column=string_column(80, nullable=False, index=True))
    api_format: ApiFormat = Field(
        default=ApiFormat.OPENAI, sa_column=enum_column(ApiFormat)
    )
    auth_type: AuthType = Field(
        default=AuthType.BEARER, sa_column=enum_column(AuthType)
    )
    base_url: str = Field(sa_column=string_column(500, nullable=False))
    default_model: str = Field(default="", sa_column=string_column(200, nullable=False))

    # Lifecycle / routing
    status: ProviderStatus = Field(
        default=ProviderStatus.ENABLED, sa_column=enum_column(ProviderStatus, index=True)
    )
    is_enabled: bool = Field(default=True, index=True)
    priority: int = Field(default=100, index=True)

    # Behaviour overrides (fall back to global settings when null)
    timeout_seconds: int | None = Field(default=None)
    max_retries: int | None = Field(default=None)

    # Free-form provider-specific configuration (headers, api_version, etc.)
    config: dict[str, Any] = Field(default_factory=dict, sa_column=json_column())
    extra_headers: dict[str, Any] = Field(default_factory=dict, sa_column=json_column())

    # Relationships
    api_keys: list["ApiKey"] = Relationship(
        back_populates="provider",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    models: list["Model"] = Relationship(
        back_populates="provider",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
