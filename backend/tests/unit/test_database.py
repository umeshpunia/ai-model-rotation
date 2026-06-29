import pytest
from sqlalchemy import text
from app.core.config import get_settings
from app.core.database import get_engine, session_scope, dispose_engine

@pytest.fixture(autouse=True)
def setup_test_db():
    # Force use of SQLite in-memory database for local database tests
    settings = get_settings()
    original_url = settings.database.database_test_url
    settings.database.database_test_url = "sqlite:///:memory:"
    dispose_engine()
    yield
    settings.database.database_test_url = original_url
    dispose_engine()

def test_database_engine_and_session():
    engine = get_engine()
    assert engine is not None
    
    with session_scope() as session:
        res = session.execute(text("SELECT 1")).scalar()
        assert res == 1

def test_session_scope_rollback():
    with pytest.raises(RuntimeError):
        with session_scope() as session:
            raise RuntimeError("Database error simulation")
