import os
import shutil
import pytest
from datetime import datetime, timezone, timedelta
from app.core.database import session_scope, get_settings, dispose_engine
from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.entities.request_log import RequestLog
from app.domain.entities.statistic import Statistic
from app.domain.enums import ApiFormat, AuthType, KeyStatus, HealthStatus
from app.services.scheduler_jobs import (
    health_check_job,
    stats_aggregation_job,
    log_cleanup_job,
    backup_job
)
from app.core.scheduler import get_scheduler_manager
from app.repositories.provider_repository import ProviderRepository
from app.repositories.api_key_repository import ApiKeyRepository
from sqlmodel import select

@pytest.fixture(autouse=True)
def setup_test_db():
    settings = get_settings()
    original_url = settings.database.database_test_url
    settings.database.database_test_url = "sqlite:///:memory:"
    dispose_engine()
    
    from sqlmodel import SQLModel
    from app.core.database import get_engine
    SQLModel.metadata.create_all(get_engine())
    yield
    SQLModel.metadata.drop_all(get_engine())
    settings.database.database_test_url = original_url
    dispose_engine()

@pytest.mark.asyncio
async def test_health_check_recovery():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        key_repo = ApiKeyRepository(session)
        
        provider = Provider(
            name="OpenAI", slug="openai", plugin="openai", api_format=ApiFormat.OPENAI, auth_type=AuthType.BEARER, base_url="https://api.openai.com/v1"
        )
        provider_repo.add(provider)
        
        assert provider.id is not None
        
        # Key in cooldown that has expired cooldown_until -> triggers validation
        key = ApiKey(
            provider_id=provider.id,
            name="Key 1",
            encrypted_key="enc1",
            key_hint="hint1",
            fingerprint="fp1",
            status=KeyStatus.COOLDOWN,
            cooldown_until=datetime.now(timezone.utc) - timedelta(seconds=1)
        )
        key_repo.add(key)
        
        # Run health check job manually
        await health_check_job(session)

def test_stats_aggregation_computations():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        
        provider = Provider(
            name="OpenAI", slug="openai", plugin="openai", api_format=ApiFormat.OPENAI, auth_type=AuthType.BEARER, base_url="https://api.openai.com/v1"
        )
        provider_repo.add(provider)
        
        assert provider.id is not None
        
        # Write mock RequestLog items
        log1 = RequestLog(
            provider_id=provider.id,
            model="gpt-4o",
            task_type="general",
            endpoint="/chat/completions",
            method="POST",
            success=True,
            status_code=200,
            latency_ms=150.0,
            cost=0.002
        )
        log2 = RequestLog(
            provider_id=provider.id,
            model="gpt-4o",
            task_type="general",
            endpoint="/chat/completions",
            method="POST",
            success=False,
            status_code=500,
            latency_ms=300.0,
            cost=0.0
        )
        session.add_all([log1, log2])
        session.flush()
        
        # Run stats aggregation
        stats_aggregation_job(session)
        
        # Verify stats generated
        stats = session.exec(select(Statistic)).all()
        assert len(stats) == 1
        assert stats[0].request_count == 2
        assert stats[0].success_count == 1
        assert stats[0].failure_count == 1
        assert stats[0].avg_latency_ms == 225.0
        assert stats[0].total_cost == 0.002

def test_sqlite_database_backup_job():
    db_file = "test_scheduler_sqlite.db"
    backup_dir = "./test_scheduler_backups"
    
    with open(db_file, "w") as f:
        f.write("mock-db-contents")
        
    try:
        backup_job(db_file, backup_dir, keep_count=2, compress=True)
        files = os.listdir(backup_dir)
        assert len(files) == 1
        assert files[0].endswith(".zip")
    finally:
        if os.path.exists(db_file):
            os.remove(db_file)
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)

def test_scheduler_manager_initialization():
    mgr = get_scheduler_manager()
    assert mgr.scheduler is not None
    assert mgr.settings is not None
