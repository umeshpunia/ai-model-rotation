from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.domain.enums import BackupType

class BackupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    path: str
    backup_type: BackupType
    size_bytes: int
    checksum: str
    compressed: bool
    note: str
    created_at: datetime
