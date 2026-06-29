"""Repository for :class:`ApiKey` entities."""
from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import or_

from app.domain.entities.api_key import ApiKey
from app.domain.enums import KeyStatus
from app.repositories.base import BaseRepository


class ApiKeyRepository(BaseRepository[ApiKey]):
    """Data access for API keys, including rotation-oriented queries."""

    model = ApiKey

    def list_for_provider(self, provider_id: int) -> list[ApiKey]:
        """Return all keys for a provider ordered by priority."""
        return self.list(
            filters={"provider_id": provider_id},
            order_by=ApiKey.priority.asc(),
        )

    def list_usable(self, provider_id: int, *, now: datetime | None = None) -> list[ApiKey]:
        """Return keys eligible to serve a request for the given provider.

        A key is usable when it is enabled, healthy, and not in an active
        cooldown window. Ordered by priority so the routing engine can pick the
        most preferred key first.
        """
        moment = now or datetime.now(timezone.utc)
        return self.list(
            filters={"provider_id": provider_id, "is_enabled": True, "status": KeyStatus.HEALTHY},
            expressions=[or_(ApiKey.cooldown_until.is_(None), ApiKey.cooldown_until <= moment)],
            order_by=ApiKey.priority.asc(),
        )

    def list_in_cooldown(self, *, now: datetime | None = None) -> list[ApiKey]:
        """Return keys whose cooldown has expired and are ready for recovery."""
        moment = now or datetime.now(timezone.utc)
        return self.list(
            filters={"status": KeyStatus.COOLDOWN},
            expressions=[ApiKey.cooldown_until.is_not(None), ApiKey.cooldown_until <= moment],
            order_by=ApiKey.cooldown_until.asc(),
        )

    def get_by_fingerprint(self, provider_id: int, fingerprint: str) -> ApiKey | None:
        """Return a key by provider + fingerprint (dedupe on add)."""
        return self.get_by(provider_id=provider_id, fingerprint=fingerprint)

    def count_for_provider(self, provider_id: int) -> int:
        """Count keys belonging to a provider."""
        return self.count(filters={"provider_id": provider_id})

    def count_healthy(self) -> int:
        """Count globally healthy, enabled keys."""
        return self.count(filters={"status": KeyStatus.HEALTHY, "is_enabled": True})

    def count_disabled(self) -> int:
        """Count keys that are disabled."""
        return self.count(filters={"is_enabled": False})
