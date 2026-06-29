from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Any, cast

from app.core.database import get_db
from app.domain.entities.backup import Backup
from app.domain.entities.user import User
from app.domain.enums import UserRole
from app.repositories.backup_repository import BackupRepository
from app.schemas.backup import BackupRead
from app.services.backup_service import BackupService
from app.services.auth_service import require_role

router = APIRouter()

@router.get("", response_model=list[BackupRead])
def list_backups(
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> list[Backup]:
    """Retrieve list of all backup snapshots."""
    repo = BackupRepository(session)
    return repo.list(order_by=cast(Any, Backup.created_at).desc())

@router.post("", response_model=BackupRead, status_code=status.HTTP_201_CREATED)
def create_manual_backup(
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Backup:
    """Trigger a new manual database backup snapshot."""
    service = BackupService(session)
    try:
        backup = service.create_backup(is_automatic=False)
        session.commit()
        return backup
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backup(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> None:
    """Delete a backup snapshot file and database record."""
    service = BackupService(session)
    try:
        service.delete_backup(id)
        session.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/{id}/restore", status_code=status.HTTP_204_NO_CONTENT)
def restore_backup(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> None:
    """Restore the application database state to a specific backup snapshot."""
    service = BackupService(session)
    try:
        # Note: session is disposed within service, so we don't commit it here
        service.restore_backup(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
