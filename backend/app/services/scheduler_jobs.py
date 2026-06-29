import os
import shutil
import zipfile
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, cast
from sqlalchemy import delete, func, select as sa_select
from sqlmodel import Session, select

from app.domain.entities.api_key import ApiKey
from app.domain.entities.provider import Provider
from app.domain.entities.model import Model
from app.domain.entities.request_log import RequestLog
from app.domain.entities.health_log import HealthLog
from app.domain.entities.statistic import Statistic
from app.domain.entities.notification import Notification
from app.domain.enums import KeyStatus, HealthStatus, StatisticWindow
from app.services.api_key_service import ApiKeyService
from app.core.logging import get_logger

_logger = get_logger("scheduler")

def _to_naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

async def health_check_job(session: Session) -> None:
    """Validate keys in cooldown or unknown state and recover them if healthy."""
    _logger.info("job.health_check.start")
    
    # Query keys on cooldown or unknown
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stmt = select(ApiKey).where(
        cast(Any, (ApiKey.is_enabled == True) &
        ((ApiKey.status == KeyStatus.COOLDOWN) | (ApiKey.status == KeyStatus.UNKNOWN)))
    )
    keys_to_check = session.exec(stmt).all()
    
    if not keys_to_check:
        _logger.info("job.health_check.idle")
        return
        
    api_key_service = ApiKeyService(session)
    for key in keys_to_check:
        # Check if cooldown is finished
        cooldown_val = _to_naive_utc(key.cooldown_until)
        if key.status == KeyStatus.COOLDOWN and cooldown_val and cooldown_val > now:
            continue
            
        try:
            assert key.id is not None
            _logger.info("job.health_check.testing_key", key_id=key.id, key_name=key.name)
            await api_key_service.test_key(key.id)
        except Exception as e:
            assert key.id is not None
            _logger.error("job.health_check.test_failed", key_id=key.id, error=str(e))
            
    _logger.info("job.health_check.complete")

def stats_aggregation_job(session: Session) -> None:
    """Summarize request logs into periodic statistics records."""
    _logger.info("job.stats_aggregation.start")
    
    now = datetime.now(timezone.utc)
    start_interval = now - timedelta(minutes=10)
    
    stmt = (
        sa_select(
            cast(Any, RequestLog.provider_id),
            cast(Any, RequestLog.model),
            cast(Any, func.count(cast(Any, RequestLog.id)).label("req_count")),
            cast(Any, func.sum(cast(Any, RequestLog.success == True)).label("succ_count")),
            cast(Any, func.avg(RequestLog.latency_ms).label("avg_latency")),
            cast(Any, func.max(RequestLog.latency_ms).label("max_latency")),
            cast(Any, func.sum(RequestLog.cost).label("cost_sum")),
            cast(Any, func.sum(RequestLog.prompt_tokens).label("prompt_tok")),
            cast(Any, func.sum(RequestLog.completion_tokens).label("comp_tok")),
            cast(Any, func.sum(RequestLog.total_tokens).label("tot_tok"))
        )
        .where(cast(Any, RequestLog.created_at >= start_interval))
        .group_by(cast(Any, RequestLog.provider_id), cast(Any, RequestLog.model))
    )
    
    aggregations = session.execute(stmt).all()
    for row in aggregations:
        provider_id, model_name, req_count, succ_count, avg_latency, max_latency, cost_sum, prompt_tok, comp_tok, tot_tok = row
        if not provider_id:
            continue
            
        stat = Statistic(
            provider_id=provider_id,
            model=model_name,
            window=StatisticWindow.HOUR,
            bucket=start_interval,
            request_count=req_count or 0,
            success_count=succ_count or 0,
            failure_count=(req_count or 0) - (succ_count or 0),
            avg_latency_ms=avg_latency or 0.0,
            max_latency_ms=max_latency or 0.0,
            total_cost=cost_sum or 0.0,
            prompt_tokens=prompt_tok or 0,
            completion_tokens=comp_tok or 0,
            total_tokens=tot_tok or 0
        )
        session.add(stat)
        
    session.commit()
    _logger.info("job.stats_aggregation.complete")
 
def log_cleanup_job(session: Session, retention_days: int = 14) -> None:
    """Prune RequestLogs and HealthLogs older than configured limit."""
    _logger.info("job.log_cleanup.start", retention_days=retention_days)
    limit = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    res1 = session.exec(delete(RequestLog).where(cast(Any, RequestLog.created_at < limit)))
    res2 = session.exec(delete(HealthLog).where(cast(Any, HealthLog.created_at < limit)))
    session.commit()
    
    _logger.info("job.log_cleanup.complete", deleted_requests=res1.rowcount, deleted_health=res2.rowcount)
 
def notification_cleanup_job(session: Session, retention_days: int = 30) -> None:
    """Prune Notification entities older than retention period."""
    _logger.info("job.notification_cleanup.start", retention_days=retention_days)
    limit = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    res = session.exec(delete(Notification).where(cast(Any, Notification.created_at < limit)))
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
        shutil.copy2(db_path, dest_path)
        
        if compress:
            zip_filename = f"{dest_path}.zip"
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(dest_path, arcname=dest_filename)
            os.remove(dest_path)
            _logger.info("job.backup.zipped", archive=zip_filename)
        else:
            _logger.info("job.backup.copied", path=dest_path)
            
        files = []
        for f in os.listdir(backup_dir):
            if f.startswith("backup_") and (f.endswith(".db") or f.endswith(".db.zip")):
                files.append(os.path.join(backup_dir, f))
                
        files.sort(key=os.path.getmtime)
        while len(files) > keep_count:
            oldest = files.pop(0)
            os.remove(oldest)
            _logger.info("job.backup.rotated_out", path=oldest)
            
    except Exception as e:
        _logger.error("job.backup.failed", error=str(e))
