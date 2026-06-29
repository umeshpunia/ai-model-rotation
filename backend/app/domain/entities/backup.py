"""Backup entity: metadata for a generated configuration/database backup."""
from __future__ import annotations
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.domain.enums import BackupType
from app.domain.entities.base import IDMixin, utcnow
from app.domain.entities.types import enum_column, string_column


class Backup(IDMixin, table=True):
    """Record of a backup artifact stored on disk."""

    __tablename__ = "backups"

    created_at: datetime = Field(default_factory=utcnow, nullable=False, index=True)

    filename: str = Field(sa_column=string_column(255, nullable=False))
    path: str = Field(sa_column=string_column(1000, nullable=False))
    backup_type: BackupType = Field(
        default=BackupType.MANUAL, sa_column=enum_column(BackupType, index=True)
    )
    size_bytes: int = Field(default=0)
    checksum: str = Field(default="", sa_column=string_column(128, nullable=False))
    compressed: bool = Field(default=True)
    note: str = Field(default="", sa_column=string_column(500, nullable=False))
