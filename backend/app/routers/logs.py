from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import Any, cast

from app.core.database import get_db
from app.domain.entities.request_log import RequestLog
from app.domain.entities.user import User
from app.domain.enums import UserRole
from app.repositories.request_log_repository import RequestLogRepository
from app.schemas.log import RequestLogRead
from app.services.auth_service import require_role

router = APIRouter()

@router.get("", response_model=list[RequestLogRead])
def list_logs(
    provider_id: int | None = Query(None),
    success: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> list[RequestLog]:
    """Retrieve all request log audit entries with pagination."""
    repo = RequestLogRepository(session)
    filters: dict[str, Any] = {}
    if provider_id is not None:
        filters["provider_id"] = provider_id
    if success is not None:
        filters["success"] = success
        
    # Sort logs descending by created_at (most recent first)
    return repo.list(filters=filters, order_by=cast(Any, RequestLog.created_at).desc(), limit=limit, offset=skip)
