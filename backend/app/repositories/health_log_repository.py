"""Repository for :class:`HealthLog` entities."""
from __future__ import annotations
from datetime import datetime

from app.domain.entities.health_log import HealthLog
from app.repositories.base import BaseRepository


class HealthLogRepository(BaseRepository[HealthLog]):
    """Data access for health-check results."""

    model = HealthLog

    def recent_for_key(self, api_key_id: int, *, limit: int = 20) -> list[HealthLog]:
        """Return recent health logs for a specific key."""
        return self.list(
            filters={"api_key_id": api_key_id},
            order_by=HealthLog.created_at.desc(),
            limit=limit,
        )

    def recent_for_provider(self, provider_id: int, *, limit: int = 20) -> list[HealthLog]:
        """Return recent health logs for a specific provider."""
        return self.list(
            filters={"provider_id": provider_id},
            order_by=HealthLog.created_at.desc(),
            limit=limit,
        )

    def recent(self, *, limit: int = 50) -> list[HealthLog]:
        """Return the most recent health logs across the system."""
        return self.list(order_by=HealthLog.created_at.desc(), limit=limit)

    def delete_older_than(self, cutoff: datetime) -> int:
        """Delete health logs older than ``cutoff``; return rows removed."""
        stale = self.list(expressions=[HealthLog.created_at < cutoff])
        for row in stale:
            self.session.delete(row)
        self.session.flush()
        return len(stale)
