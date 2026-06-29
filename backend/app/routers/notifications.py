from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import Any

from app.core.database import get_db
from app.domain.entities.notification import Notification
from app.domain.entities.user import User
from app.domain.enums import UserRole
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationRead
from app.services.auth_service import require_role

router = APIRouter()

@router.get("", response_model=list[NotificationRead])
def list_notifications(
    is_read: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> list[Notification]:
    """Retrieve notifications log with pagination."""
    repo = NotificationRepository(session)
    filters = {}
    if is_read is not None:
        filters["is_read"] = is_read
    return repo.list(filters=filters, order_by=Notification.created_at.desc(), limit=limit, offset=skip)

@router.put("/{id}/read", response_model=NotificationRead)
def mark_notification_read(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Notification:
    """Mark a notification as read."""
    repo = NotificationRepository(session)
    notif = repo.get(id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with id {id} not found."
        )
    repo.update(notif, {"is_read": True})
    return notif
