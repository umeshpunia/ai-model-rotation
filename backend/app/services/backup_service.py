import os
import shutil
import zipfile
import tempfile
from datetime import datetime, timezone
from typing import Any, cast
from sqlmodel import Session

from app.core.config import get_settings
from app.core.database import dispose_engine, init_engine, session_scope
from app.domain.entities.backup import Backup
from app.domain.enums import BackupType
from app.repositories.backup_repository import BackupRepository
from app.core.logging import get_logger

_logger = get_logger("backup_service")

class BackupService:
    """Manages the lifecycle of database backups, including manual creation, rotation, and restores."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = BackupRepository(session)

    def _get_live_db_path(self) -> str:
        """Resolve the local file path to the SQLite database."""
        url = get_settings().database_url
        if not url.startswith("sqlite"):
            raise RuntimeError("Backups only supported for SQLite databases.")
        # Strip sqlite scheme and query parameters
        clean_path = url.replace("sqlite:///", "").split("?")[0]
        return os.path.abspath(clean_path)

    def create_backup(self, is_automatic: bool = False, note: str = "") -> Backup:
        """Create a new database backup copy, compress it, and register in database."""
        settings = get_settings().backup
        db_path = self._get_live_db_path()
        backup_dir = os.path.abspath(settings.backup_directory)
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_filename = f"backup_{timestamp}.db"
        dest_path = os.path.join(backup_dir, dest_filename)
        
        _logger.info("backup.create.start", db_path=db_path, dest_path=dest_path)
        
        try:
            # 1. First, create and commit the backup metadata record so the database file contains it.
            b_type = BackupType.SCHEDULED if is_automatic else BackupType.MANUAL
            final_filename = f"{dest_filename}.zip" if settings.backup_compression else dest_filename
            final_path = f"{dest_path}.zip" if settings.backup_compression else dest_path

            backup = Backup(
                filename=final_filename,
                path=final_path,
                backup_type=b_type,
                size_bytes=0,
                checksum="",
                compressed=settings.backup_compression,
                note=note,
            )
            self.repo.add(backup)
            self.session.commit()
            
            # Retrieve from session to make sure it's fully populated and valid
            self.session.refresh(backup)
            
            # 2. Copy the active SQLite database file
            shutil.copy2(db_path, dest_path)
            
            # 3. Handle compression if enabled
            if settings.backup_compression:
                with zipfile.ZipFile(final_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(dest_path, arcname=dest_filename)
                os.remove(dest_path)
                
            # 4. Update the record with actual file size
            size = os.path.getsize(final_path)
            backup.size_bytes = size
            self.session.add(backup)
            self.session.commit()
            self.session.refresh(backup)
            
            _logger.info("backup.create.success", backup_id=backup.id, path=final_path)
            
            # Prune old backups beyond retention count
            self.prune_old_backups(settings.backup_keep_count)
            
            return backup
            
        except Exception as e:
            _logger.error("backup.create.failed", error=str(e))
            raise RuntimeError(f"Backup generation failed: {str(e)}")

    def prune_old_backups(self, keep_count: int) -> None:
        """Prune older backups from disk and database according to retention policy."""
        backups = self.repo.list(order_by=cast(Any, Backup.created_at).asc())
        while len(backups) > keep_count:
            oldest = backups.pop(0)
            _logger.info("backup.pruning", oldest_id=oldest.id, path=oldest.path)
            
            # Remove file
            if oldest.path and os.path.exists(oldest.path):
                try:
                    os.remove(oldest.path)
                except Exception as e:
                    _logger.warning("backup.prune_file.failed", path=oldest.path, error=str(e))
                    
            self.repo.delete(oldest)
            self.session.commit()

    def delete_backup(self, backup_id: int) -> None:
        """Remove a backup archive file and delete its database registration."""
        backup = self.repo.get(backup_id)
        if not backup:
            raise ValueError(f"Backup with ID {backup_id} not found.")
            
        if backup.path and os.path.exists(backup.path):
            try:
                os.remove(backup.path)
            except Exception as e:
                _logger.warning("backup.delete_file.failed", path=backup.path, error=str(e))
                
        self.repo.delete(backup)
        self.session.commit()
        _logger.info("backup.delete.success", backup_id=backup_id)

    def restore_backup(self, backup_id: int) -> None:
        """Close active database engine, replace live database with backup copy, and re-initialize engine."""
        backup = self.repo.get(backup_id)
        if not backup:
            raise ValueError(f"Backup with ID {backup_id} not found.")
            
        if not backup.path or not os.path.exists(backup.path):
            raise FileNotFoundError(f"Backup file not found on disk at: {backup.path}")
            
        db_path = self._get_live_db_path()
        _logger.info("backup.restore.start", backup_id=backup_id, live_db=db_path)
        
        # Temp dir for extraction if zipped
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_db = os.path.join(temp_dir, "restore.db")
            
            if backup.path.endswith(".zip"):
                with zipfile.ZipFile(backup.path, 'r') as zipf:
                    # Find first .db in ZIP
                    db_names = [name for name in zipf.namelist() if name.endswith(".db")]
                    if not db_names:
                        raise RuntimeError("No SQLite database file found inside the zip archive.")
                    # Extract to temp path
                    with open(temp_db, "wb") as f_out:
                        f_out.write(zipf.read(db_names[0]))
            else:
                shutil.copy2(backup.path, temp_db)
                
            # Safely replace active database
            dispose_engine()
            try:
                shutil.copy2(temp_db, db_path)
                _logger.info("backup.restore.db_replaced")
            finally:
                init_engine()
