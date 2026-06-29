"""Backup request/response DTOs."""
from datetime import datetime

from pydantic import Field

from app.domain.enums import BackupType
from app.schemas.common import ORMSchema, SchemaBase


class BackupCreate(SchemaBase):
    """Payload for triggering a manual backup."""

    note: str = Field(default="", max_length=500)
    compress: bool = True


class BackupRead(ORMSchema):
    """Backup metadata as returned by the API."""

    id: int
    created_at: datetime
    filename: str
    path: str
    backup_type: BackupType
    size_bytes: int
    checksum: str
    compressed: bool
    note: str
