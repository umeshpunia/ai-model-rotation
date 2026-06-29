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
