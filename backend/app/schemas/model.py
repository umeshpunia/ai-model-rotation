"""Provider model request/response DTOs."""
from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import ORMSchema, SchemaBase


class ModelBase(SchemaBase):
    """Fields shared by model create/update."""

    name: str = Field(min_length=1, max_length=200)
    display_name: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=500)
    is_enabled: bool = True
    context_window: int | None = Field(default=None, ge=0)
    max_output_tokens: int | None = Field(default=None, ge=0)
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_tools: bool = False
    supports_embeddings: bool = False
    supports_images: bool = False
    input_cost_per_1k: float = Field(default=0.0, ge=0)
    output_cost_per_1k: float = Field(default=0.0, ge=0)
    task_types: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class ModelCreate(ModelBase):
    """Payload for adding a model to a provider."""

    provider_id: int = Field(gt=0)


class ModelUpdate(SchemaBase):
    """Partial update payload for a model."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    display_name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=500)
    is_enabled: bool | None = None
    context_window: int | None = Field(default=None, ge=0)
    max_output_tokens: int | None = Field(default=None, ge=0)
    supports_streaming: bool | None = None
    supports_vision: bool | None = None
    supports_tools: bool | None = None
    supports_embeddings: bool | None = None
    supports_images: bool | None = None
    input_cost_per_1k: float | None = Field(default=None, ge=0)
    output_cost_per_1k: float | None = Field(default=None, ge=0)
    task_types: list[str] | None = None
    meta: dict[str, Any] | None = None


class ModelRead(ORMSchema):
    """Model as returned by the API."""

    id: int
    provider_id: int
    name: str
    display_name: str
    description: str
    is_enabled: bool
    context_window: int | None
    max_output_tokens: int | None
    supports_streaming: bool
    supports_vision: bool
    supports_tools: bool
    supports_embeddings: bool
    supports_images: bool
    input_cost_per_1k: float
    output_cost_per_1k: float
    task_types: list[str]
    meta: dict[str, Any]
    created_at: datetime
    updated_at: datetime
