"""Repository for :class:`RequestLog` entities."""
from __future__ import annotations
from datetime import datetime

from app.domain.entities.request_log import RequestLog
from app.repositories.base import BaseRepository


class RequestLogRepository(BaseRepository[RequestLog]):
    """Data access for request logs (append-mostly, periodically pruned)."""

    model = RequestLog

    def recent(self, *, limit: int = 50) -> list[RequestLog]:
        """Return the most recent request logs."""
        return self.list(order_by=RequestLog.created_at.desc(), limit=limit)

    def list_since(self, since: datetime) -> list[RequestLog]:
        """Return request logs created at/after ``since``."""
        return self.list(
            expressions=[RequestLog.created_at >= since],
            order_by=RequestLog.created_at.asc(),
        )

    def count_since(self, since: datetime) -> int:
        """Count request logs created at/after ``since``."""
        return self.count(expressions=[RequestLog.created_at >= since])

    def delete_older_than(self, cutoff: datetime) -> int:
        """Delete logs older than ``cutoff``; return number of rows removed."""
        stale = self.list(expressions=[RequestLog.created_at < cutoff])
        for row in stale:
            self.session.delete(row)
        self.session.flush()
        return len(stale)
