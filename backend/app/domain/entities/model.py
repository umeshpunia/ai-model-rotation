"""Model entity: a concrete model offered by a provider (e.g. gpt-4o, claude...)."""
from typing import TYPE_CHECKING, Any

from sqlmodel import Field, Relationship, SQLModel

from app.domain.entities.base import IDMixin, TimestampMixin
from app.domain.entities.types import json_column, string_column

if TYPE_CHECKING:
    from app.domain.entities.provider import Provider


class Model(IDMixin, TimestampMixin, table=True):
    """A model exposed by a provider.

    Capabilities and pricing are stored (never hardcoded) so the routing engine
    can make cost-, capability-, and task-aware decisions dynamically.
    """

    __tablename__ = "models"

    provider_id: int = Field(foreign_key="providers.id", index=True, nullable=False)

    name: str = Field(sa_column=string_column(200, nullable=False, index=True))
    display_name: str = Field(default="", sa_column=string_column(200, nullable=False))
    description: str = Field(default="", sa_column=string_column(500, nullable=False))

    is_enabled: bool = Field(default=True, index=True)

    # Capabilities
    context_window: int | None = Field(default=None)
    max_output_tokens: int | None = Field(default=None)
    supports_streaming: bool = Field(default=True)
    supports_vision: bool = Field(default=False)
    supports_tools: bool = Field(default=False)
    supports_embeddings: bool = Field(default=False)
    supports_images: bool = Field(default=False)

    # Pricing (USD per 1K tokens)
    input_cost_per_1k: float = Field(default=0.0)
    output_cost_per_1k: float = Field(default=0.0)

    # Task categories this model is suited for (TaskType values)
    task_types: list[str] = Field(default_factory=list, sa_column=json_column())
    # Arbitrary provider metadata
    meta: dict[str, Any] = Field(default_factory=dict, sa_column=json_column())

    # Relationships
    provider: "Provider" = Relationship(back_populates="models")
