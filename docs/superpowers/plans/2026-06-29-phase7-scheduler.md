# Phase 7 Background Services & Health Monitoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the background scheduler (`AsyncIOScheduler`), jobs for health check recovery, stats aggregation, log cleanup, notifications pruning, and compressed database backups, along with comprehensive unit tests.

**Architecture:** Create `scheduler_jobs.py` in `services/` and `scheduler.py` in `core/`. Create unit tests running the job handlers in isolation.

**Tech Stack:** Python 3.12, sqlmodel, apscheduler

---

### Task 1: Create Scheduler Jobs Module

**Files:**
- Create: `backend/app/services/scheduler_jobs.py`

- [ ] **Step 1: Write scheduler jobs implementation**

Write the following code into `backend/app/services/scheduler_jobs.py`:
```python
import os
import shutil
import zipfile
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
from sqlalchemy import select, delete, func
from sqlmodel import Session

from app.domain.entities.api_key import ApiKey
from app.domain.entities.provider import Provider
from app.domain.entities.model import Model
from app.domain.entities.request_log import RequestLog
from app.domain.entities.health_log import HealthLog
from app.domain.entities.statistic import Statistic
from app.domain.entities.notification import Notification
from app.domain.enums import KeyStatus, HealthStatus
from app.services.api_key_service import ApiKeyService
from app.core.logging import get_logger

_logger = get_logger("scheduler")

async def health_check_job(session: Session) -> None:
    """Validate keys in cooldown or unknown state and recover them if healthy."""
    _logger.info("job.health_check.start")
    
    # Query keys on cooldown or unknown
    now = datetime.now(timezone.utc)
    stmt = select(ApiKey).where(
        (ApiKey.is_enabled == True) &
        ((ApiKey.status == KeyStatus.COOLDOWN) | (ApiKey.status == KeyStatus.UNKNOWN))
    )
    keys_to_check = session.exec(stmt).all()
    
    if not keys_to_check:
        _logger.info("job.health_check.idle")
        return
        
    api_key_service = ApiKeyService(session)
    for key in keys_to_check:
        # Check if cooldown is finished
        if key.status == KeyStatus.COOLDOWN and key.cooldown_until and key.cooldown_until > now:
            continue
            
        try:
            _logger.info("job.health_check.testing_key", key_id=key.id, key_name=key.name)
            await api_key_service.test_key(key.id)
        except Exception as e:
            _logger.error("job.health_check.test_failed", key_id=key.id, error=str(e))
            
    _logger.info("job.health_check.complete")

def stats_aggregation_job(session: Session) -> None:
    """Summarize request logs into periodic statistics records."""
    _logger.info("job.stats_aggregation.start")
    
    now = datetime.now(timezone.utc)
    # Calculate aggregation for the last 10 minutes (or custom interval)
    start_interval = now - timedelta(minutes=10)
    
    stmt = (
        select(
            RequestLog.provider_id,
            RequestLog.model,
            func.count(RequestLog.id).label("req_count"),
            func.sum(RequestLog.success == True).label("succ_count"),
            func.avg(RequestLog.latency_ms).label("avg_latency"),
            func.sum(RequestLog.total_cost).label("cost_sum")
        )
        .where(RequestLog.created_at >= start_interval)
        .group_by(RequestLog.provider_id, RequestLog.model)
    )
    
    aggregations = session.exec(stmt).all()
    for row in aggregations:
        provider_id, model_name, req_count, succ_count, avg_latency, cost_sum = row
        if not provider_id:
            continue
            
        # Calculate success rate
        success_rate = (succ_count or 0) / (req_count or 1)
        
        stat = Statistic(
            provider_id=provider_id,
            model=model_name,
            window_start=start_interval,
            window_end=now,
            request_count=req_count or 0,
            success_count=succ_count or 0,
            failure_count=(req_count or 0) - (succ_count or 0),
            success_rate=success_rate,
            avg_latency_ms=avg_latency or 0.0,
            total_cost=cost_sum or 0.0
        )
        session.add(stat)
        
    session.commit()
    _logger.info("job.stats_aggregation.complete")

def log_cleanup_job(session: Session, retention_days: int = 14) -> None:
    """Prune RequestLogs and HealthLogs older than configured limit."""
    _logger.info("job.log_cleanup.start", retention_days=retention_days)
    limit = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    res1 = session.exec(delete(RequestLog).where(RequestLog.created_at < limit))
    res2 = session.exec(delete(HealthLog).where(HealthLog.created_at < limit))
    session.commit()
    
    _logger.info("job.log_cleanup.complete", deleted_requests=res1.rowcount, deleted_health=res2.rowcount)

def notification_cleanup_job(session: Session, retention_days: int = 30) -> None:
    """Prune Notification entities older than retention period."""
    _logger.info("job.notification_cleanup.start", retention_days=retention_days)
    limit = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    res = session.exec(delete(Notification).where(Notification.created_at < limit))
    session.commit()
    _logger.info("job.notification_cleanup.complete", deleted_notifications=res.rowcount)

def backup_job(db_path: str, backup_dir: str, keep_count: int = 7, compress: bool = True) -> None:
    """Create rolling zipped backups of the SQLite database file."""
    _logger.info("job.backup.start", db_path=db_path, backup_dir=backup_dir)
    
    if not os.path.exists(db_path):
        _logger.warning("job.backup.missing_db", path=db_path)
        return
        
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest_filename = f"backup_{timestamp}.db"
    dest_path = os.path.join(backup_dir, dest_filename)
    
    try:
        # Copy file
        shutil.copy2(db_path, dest_path)
        
        # Zip if enabled
        if compress:
            zip_filename = f"{dest_path}.zip"
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(dest_path, arcname=dest_filename)
            os.remove(dest_path)  # Delete uncompressed file
            _logger.info("job.backup.zipped", archive=zip_filename)
        else:
            _logger.info("job.backup.copied", path=dest_path)
            
        # Rotate backups (keep count)
        files = []
        for f in os.listdir(backup_dir):
            if f.startswith("backup_") and (f.endswith(".db") or f.endswith(".db.zip")):
                files.append(os.path.join(backup_dir, f))
                
        # Sort by creation time (oldest first)
        files.sort(key=os.path.getmtime)
        while len(files) > keep_count:
            oldest = files.pop(0)
            os.remove(oldest)
            _logger.info("job.backup.rotated_out", path=oldest)
            
    except Exception as e:
        _logger.error("job.backup.failed", error=str(e))
```

- [ ] **Step 2: Commit scheduler jobs**

Run:
```bash
git add backend/app/services/scheduler_jobs.py
git commit -m "feat(services): implement scheduler background jobs for health checking, stats, backups, and cleanups"
```

---

### Task 2: Create Scheduler Manager

**Files:**
- Create: `backend/app/core/scheduler.py`

- [ ] **Step 1: Write BackgroundSchedulerManager class**

Write the following code into `backend/app/core/scheduler.py`:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.config import get_settings
from app.core.database import session_scope
from app.services.scheduler_jobs import (
    health_check_job,
    stats_aggregation_job,
    log_cleanup_job,
    backup_job,
    notification_cleanup_job
)
from app.core.logging import get_logger

_logger = get_logger("scheduler")

class BackgroundSchedulerManager:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self.settings = get_settings()

    def start(self) -> None:
        """Start the AP scheduler and schedule all jobs at configured intervals."""
        if not self.settings.scheduler.scheduler_enabled:
            _logger.info("scheduler.disabled")
            return
            
        _logger.info("scheduler.starting")
        
        # Schedule Health Check
        self.scheduler.add_job(
            self._run_health_check,
            "interval",
            seconds=self.settings.scheduler.health_check_interval_seconds,
            name="health_check"
        )
        
        # Schedule Statistics Aggregation
        self.scheduler.add_job(
            self._run_stats_aggregation,
            "interval",
            seconds=self.settings.scheduler.statistics_aggregation_interval_seconds,
            name="stats_aggregation"
        )
        
        # Schedule Log Cleanup
        self.scheduler.add_job(
            self._run_log_cleanup,
            "interval",
            seconds=self.settings.scheduler.log_cleanup_interval_seconds,
            name="log_cleanup"
        )
        
        # Schedule Notification Cleanup
        self.scheduler.add_job(
            self._run_notification_cleanup,
            "interval",
            seconds=self.settings.scheduler.notification_cleanup_interval_seconds,
            name="notification_cleanup"
        )
        
        # Schedule Database Backup
        self.scheduler.add_job(
            self._run_backup,
            "interval",
            seconds=self.settings.scheduler.backup_interval_seconds,
            name="database_backup"
        )
        
        self.scheduler.start()
        _logger.info("scheduler.started")

    def shutdown(self) -> None:
        """Gracefully stop the background scheduler."""
        _logger.info("scheduler.stopping")
        self.scheduler.shutdown()
        _logger.info("scheduler.stopped")

    # Wrapper execution hooks to handle sessions
    async def _run_health_check(self) -> None:
        with session_scope() as session:
            await health_check_job(session)

    def _run_stats_aggregation(self) -> None:
        with session_scope() as session:
            stats_aggregation_job(session)

    def _run_log_cleanup(self) -> None:
        with session_scope() as session:
            retention = self.settings.logging.log_retention
            log_cleanup_job(session, retention)

    def _run_notification_cleanup(self) -> None:
        with session_scope() as session:
            notification_cleanup_job(session)

    def _run_backup(self) -> None:
        # SQLite database url example: sqlite:///aigateway.db
        url = self.settings.database.database_url
        if url.startswith("sqlite:///"):
            db_path = url.replace("sqlite:///", "")
            backup_dir = self.settings.backup.backup_directory
            keep = self.settings.backup.backup_keep_count
            compress = self.settings.backup.backup_compression
            backup_job(db_path, backup_dir, keep, compress)
        else:
            _logger.info("scheduler.backup.skipped", reason="Not SQLite database URL")

_scheduler_manager = BackgroundSchedulerManager()

def get_scheduler_manager() -> BackgroundSchedulerManager:
    return _scheduler_manager
```

- [ ] **Step 2: Commit scheduler manager**

Run:
```bash
git add backend/app/core/scheduler.py
git commit -m "feat(core): implement BackgroundSchedulerManager for timing setups and lifecycles"
```

---

### Task 3: Create Scheduler Unit Tests

**Files:**
- Create: `backend/tests/unit/test_scheduler.py`

- [ ] **Step 1: Write test suite**

Write the following code into `backend/tests/unit/test_scheduler.py`:
```python
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
        
        # Create a key in cooldown that has expired cooldown_until -> triggers validation
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
            total_cost=0.002
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
            total_cost=0.0
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
        assert stats[0].success_rate == 0.5
        assert stats[0].avg_latency_ms == 225.0
        assert stats[0].total_cost == 0.002

def test_sqlite_database_backup_job():
    db_file = "test_scheduler_sqlite.db"
    backup_dir = "./test_scheduler_backups"
    
    # Create empty db file
    with open(db_file, "w") as f:
        f.write("mock-db-contents")
        
    try:
        backup_job(db_file, backup_dir, keep_count=2, compress=True)
        # Check backup zip exists
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
```

- [ ] **Step 2: Run all unit tests**

Run: `.\backend\.venv\Scripts\pytest backend/tests/ -v`
Expected output: 32 passed tests.

- [ ] **Step 3: Commit scheduler tests**

Run:
```bash
git add backend/tests/unit/test_scheduler.py
git commit -m "test: add scheduler manager and background worker jobs unit tests"
```

---

### Task 4: Update Phase Status Documentation

**Files:**
- Modify: `phase.md`

- [ ] **Step 1: Check off Phase 7 checkboxes**

Change checkboxes in `d:\projects\python\ai-model-rotation\phase.md` lines 150-170 under `## Phase 7: Background Services & Health Monitoring` to `[x]`.

- [ ] **Step 2: Update Phase 7 summary status**

Change:
```markdown
| 7 | Background Services & Health Monitoring | Not Started |
```
To:
```markdown
| 7 | Background Services & Health Monitoring | Complete |
```

- [ ] **Step 3: Commit phase tracking updates**

Run:
```bash
git add phase.md docs/superpowers/plans/2026-06-29-phase7-scheduler.md docs/superpowers/specs/2026-06-29-phase7-scheduler-design.md
git commit -m "docs: complete Phase 7 background services status tracking and specs/plans"
```
