"""Repository for :class:`Model` entities."""
from __future__ import annotations

from app.domain.entities.model import Model
from app.repositories.base import BaseRepository


class ModelRepository(BaseRepository[Model]):
    """Data access for provider models."""

    model = Model

    def list_for_provider(self, provider_id: int) -> list[Model]:
        """Return all models for a provider ordered by name."""
        return self.list(
            filters={"provider_id": provider_id},
            order_by=Model.name.asc(),
        )

    def list_enabled(self) -> list[Model]:
        """Return all enabled models across providers."""
        return self.list(filters={"is_enabled": True}, order_by=Model.name.asc())

    def get_by_name(self, provider_id: int, name: str) -> Model | None:
        """Return a model by provider + model name."""
        return self.get_by(provider_id=provider_id, name=name)
