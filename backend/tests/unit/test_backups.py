import os
import shutil
import pytest
from sqlmodel import SQLModel, select

from app.core.database import session_scope, get_settings, dispose_engine, get_engine
from app.domain.entities.backup import Backup
from app.services.backup_service import BackupService

@pytest.fixture(autouse=True)
def setup_test_db():
    settings = get_settings()
    original_url = settings.database.database_url
    original_test_url = settings.database.database_test_url
    original_backup_dir = settings.backup.backup_directory
    
    db_file = "test_backups.db"
    settings.database.database_url = f"sqlite:///{db_file}"
    settings.database.database_test_url = f"sqlite:///{db_file}"
    settings.backup.backup_directory = "./test_backups_dir"
    dispose_engine()
    
    SQLModel.metadata.create_all(get_engine())
    yield
    
    SQLModel.metadata.drop_all(get_engine())
    settings.database.database_url = original_url
    settings.database.database_test_url = original_test_url
    settings.backup.backup_directory = original_backup_dir
    dispose_engine()
    
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass
            
    if os.path.exists("./test_backups_dir"):
        try:
            shutil.rmtree("./test_backups_dir")
        except Exception:
            pass

def test_backup_create_delete_and_restore():
    # 1. Create a backup
    with session_scope() as session:
        service = BackupService(session)
        backup = service.create_backup(is_automatic=False)
        assert backup.id is not None
        assert os.path.exists(backup.path)
        backup_id = backup.id
        path = backup.path

    # 2. Test List backups
    with session_scope() as session:
        service = BackupService(session)
        backups = service.repo.list()
        assert len(backups) == 1
        assert backups[0].id == backup_id

    # 3. Test database restore
    with session_scope() as session:
        service = BackupService(session)
        # Restore database
        service.restore_backup(backup_id)
        
    # Re-verify that engine works after restore re-initialization
    with session_scope() as session:
        res = session.exec(select(1)).first()
        assert res == 1

    # 4. Test delete backup
    with session_scope() as session:
        service = BackupService(session)
        service.delete_backup(backup_id)
        assert not os.path.exists(path)
        assert len(service.repo.list()) == 0
