# Design Specification: Phase 7 Background Services & Health Monitoring

## 1. Goal
Implement a dynamic background scheduler utilizing `APScheduler` inside the AI Gateway Pro FastAPI daemon. The scheduler must run periodic health check jobs (connection testing and cooldown recoveries), stats aggregation logs processing, backups, and log/notification cleanups.

## 2. Requirements & Scope
- **Scheduler Core**:
  - Load scheduler intervals dynamically from `SchedulerSettings` in `config.py`.
  - Integrate startup/shutdown lifecycles using FastAPI event hooks.
- **Background Jobs**:
  - **Health Check Job**: Check keys whose `cooldown_until <= now` or state = `UNKNOWN`. Execute live connections tests using `ApiKeyService.test_key(key.id)` and restore key states.
  - **Stats Aggregation Job**: Process `RequestLog` rows since the last interval, group metrics by provider/model/key, and insert/update `Statistic` summary tables.
  - **Log & Notification Cleanup Job**: Periodically prune database logs and notifications older than the configured threshold (e.g. `log_retention` days).
  - **Backup Job**: Automate daily copies of the database file into the backups directory. If compressed, pack into a `.zip` archive, keeping a maximum of 7 rolling copies.

## 3. Design Details

### A. Scheduler Engine Setup (`core/scheduler.py`)
- Instantiates `AsyncIOScheduler`.
- Defines job hooks using background session scopes:
  ```python
  class BackgroundSchedulerManager:
      def start(self): ...
      def shutdown(self): ...
  ```

### B. Job Logic Module (`services/scheduler_jobs.py`)
- Handles execution logic of each individual background task:
  - `health_check_job()`: Queries matching keys, decrypts, runs connections tests, and saves metrics.
  - `stats_aggregation_job()`: Analyzes logs and writes summary `Statistic` database items.
  - `cleanup_job()`: Cleans old database items.
  - `backup_job()`: Creates zipped backups.

## 4. Verification Plan
- **Unit Tests (`tests/unit/test_scheduler.py`)**:
  - Verify scheduler registers the correct count of jobs.
  - Verify database backup task creates files.
  - Verify stats aggregator successfully processes mock request logs.
  - Verify key health-check recovery transitions keys on cooldown back to healthy.
