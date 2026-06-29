"""Repository for :class:`Provider` entities."""
from __future__ import annotations

from app.domain.entities.provider import Provider
from app.domain.enums import ProviderStatus
from app.repositories.base import BaseRepository


class ProviderRepository(BaseRepository[Provider]):
    """Data access for providers, including routing-oriented queries."""

    model = Provider

    def get_by_slug(self, slug: str) -> Provider | None:
        """Return a provider by its unique slug."""
        return self.get_by(slug=slug)

    def list_enabled(self) -> list[Provider]:
        """Return enabled providers ordered by routing priority (asc)."""
        return self.list(
            filters={"is_enabled": True, "status": ProviderStatus.ENABLED},
            order_by=Provider.priority.asc(),
        )

    def list_by_priority(self) -> list[Provider]:
        """Return all providers ordered by priority then name."""
        return self.list(order_by=(Provider.priority.asc(), Provider.name.asc()))

    def slug_exists(self, slug: str, *, exclude_id: int | None = None) -> bool:
        """Whether a provider with ``slug`` exists (optionally excluding one id)."""
        existing = self.get_by_slug(slug)
        if existing is None:
            return False
        return exclude_id is None or existing.id != exclude_id
