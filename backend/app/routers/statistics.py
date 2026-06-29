from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from typing import Any
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.domain.entities.statistic import Statistic
from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.entities.request_log import RequestLog
from app.domain.entities.notification import Notification
from app.domain.enums import UserRole, KeyStatus
from app.domain.entities.user import User
from app.repositories.statistic_repository import StatisticRepository
from app.schemas.statistic import StatisticRead, DashboardStats
from app.services.auth_service import require_role

router = APIRouter()

@router.get("", response_model=list[StatisticRead])
def list_statistics(
    provider_id: int | None = Query(None),
    model: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> list[Statistic]:
    """Retrieve time-window aggregated statistics history."""
    repo = StatisticRepository(session)
    filters = {}
    if provider_id is not None:
        filters["provider_id"] = provider_id
    if model is not None:
        filters["model"] = model
    return repo.list(filters=filters, limit=limit, offset=skip)

@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard_summary(
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> DashboardStats:
    """Retrieve dashboard status KPIs and active metrics."""
    # Count totals
    total_providers = session.exec(select(Provider)).all()
    keys = session.exec(select(ApiKey)).all()
    
    # Prune naive offset time comparison for today
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
    logs_stmt = select(RequestLog).where(cast(Any, RequestLog.created_at >= today))
    # Wait, we import cast in python files. We can use typing.cast
    from typing import cast
    logs_stmt = select(RequestLog).where(cast(Any, RequestLog.created_at >= today))
    logs_today = session.exec(logs_stmt).all()
    
    # Unread notifications
    unread = session.exec(select(Notification).where(cast(Any, Notification.is_read == False))).all()
    
    total_requests = len(logs_today)
    successful_requests = sum(1 for l in logs_today if l.success)
    total_tokens = sum(l.total_tokens for l in logs_today)
    total_cost = sum(l.cost for l in logs_today)
    avg_latency = sum(l.latency_ms or 0.0 for l in logs_today) / max(total_requests, 1)
    
    success_rate = (successful_requests / max(total_requests, 1)) * 100.0
    
    # Active candidate
    active_provider = None
    active_model = None
    current_key_hint = None
    
    # Pick first enabled key
    enabled_keys = [k for k in keys if k.is_enabled and k.status == KeyStatus.HEALTHY]
    if enabled_keys:
        enabled_keys.sort(key=lambda k: k.priority)
        current_key_hint = enabled_keys[0].key_hint
        prov = session.get(Provider, enabled_keys[0].provider_id)
        if prov:
            active_provider = prov.name
            active_model = prov.default_model

    return DashboardStats(
        active_provider=active_provider,
        active_model=active_model,
        current_key_hint=current_key_hint,
        total_providers=len(total_providers),
        total_keys=len(keys),
        healthy_keys=sum(1 for k in keys if k.status == KeyStatus.HEALTHY),
        disabled_keys=sum(1 for k in keys if not k.is_enabled),
        requests_today=total_requests,
        tokens_used=total_tokens,
        average_latency_ms=avg_latency,
        total_cost=total_cost,
        success_rate=success_rate,
        unread_notifications=len(unread)
    )
