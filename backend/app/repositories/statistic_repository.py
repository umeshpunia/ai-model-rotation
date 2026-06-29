"""Repository for :class:`Statistic` entities."""
from __future__ import annotations
from datetime import datetime

from app.domain.entities.statistic import Statistic
from app.domain.enums import StatisticWindow
from app.repositories.base import BaseRepository


class StatisticRepository(BaseRepository[Statistic]):
    """Data access for pre-aggregated statistics."""

    model = Statistic

    def get_bucket(
        self,
        *,
        window: StatisticWindow,
        bucket: datetime,
        provider_id: int | None = None,
        api_key_id: int | None = None,
        model: str = "",
    ) -> Statistic | None:
        """Return the aggregate row for a precise (window, bucket, scope)."""
        return self.get_by(
            window=window,
            bucket=bucket,
            provider_id=provider_id,
            api_key_id=api_key_id,
            model=model,
        )

    def list_window(
        self,
        window: StatisticWindow,
        *,
        since: datetime | None = None,
        provider_id: int | None = None,
    ) -> list[Statistic]:
        """Return aggregates for a window, optionally scoped/time-filtered."""
        filters: dict[str, object] = {"window": window}
        if provider_id is not None:
            filters["provider_id"] = provider_id
        expressions = [Statistic.bucket >= since] if since is not None else None
        return self.list(
            filters=filters,
            expressions=expressions,
            order_by=Statistic.bucket.asc(),
        )

    def delete_older_than(self, cutoff: datetime) -> int:
        """Delete aggregates older than ``cutoff``; return rows removed."""
        stale = self.list(expressions=[Statistic.bucket < cutoff])
        for row in stale:
            self.session.delete(row)
        self.session.flush()
        return len(stale)
