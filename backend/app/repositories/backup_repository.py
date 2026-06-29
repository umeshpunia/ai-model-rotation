"""Repository for :class:`Backup` entities."""
from __future__ import annotations

from app.domain.entities.backup import Backup
from app.repositories.base import BaseRepository


class BackupRepository(BaseRepository[Backup]):
    """Data access for backup artifact metadata."""

    model = Backup

    def list_recent(self, *, limit: int = 50) -> list[Backup]:
        """Return the most recent backups, newest first."""
        return self.list(order_by=Backup.created_at.desc(), limit=limit)

    def list_oldest(self) -> list[Backup]:
        """Return all backups oldest-first (for retention pruning)."""
        return self.list(order_by=Backup.created_at.asc())
