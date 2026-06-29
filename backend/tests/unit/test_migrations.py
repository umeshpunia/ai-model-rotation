import os
import pytest
from alembic.config import Config
from alembic import command
from app.core.config import get_settings
from app.core.database import dispose_engine

def test_alembic_upgrade_downgrade():
    settings = get_settings()
    original_url = settings.database.database_test_url
    
    # Use a temporary SQLite database file for testing migration upgrade/downgrade
    db_file = "test_migration_run.db"
    settings.database.database_test_url = f"sqlite:///{db_file}"
    dispose_engine()
    
    try:
        # Load Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Run upgrade head
        command.upgrade(alembic_cfg, "head")
        
        # Run downgrade back to base
        command.downgrade(alembic_cfg, "base")
    finally:
        # Clean up database file
        dispose_engine()
        if os.path.exists(db_file):
            os.remove(db_file)
        # Restore settings
        settings.database.database_test_url = original_url
        dispose_engine()
