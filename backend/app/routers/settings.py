from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import Any

from app.core.database import get_db
from app.domain.entities.setting import Setting
from app.domain.entities.user import User
from app.domain.enums import UserRole
from app.repositories.setting_repository import SettingRepository
from app.schemas.setting import SettingRead, SettingsBulkUpdate, SettingsExport, SettingsImport
from app.services.auth_service import require_role

router = APIRouter()

@router.get("", response_model=list[SettingRead])
def get_settings(
    profile: str = Query("default"),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> list[Setting]:
    """Retrieve all global settings for a configuration profile."""
    repo = SettingRepository(session)
    return repo.list_for_profile(profile)

@router.put("", response_model=list[SettingRead])
def update_settings(
    payload: SettingsBulkUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> list[Setting]:
    """Bulk update multiple settings at once."""
    repo = SettingRepository(session)
    updated = []
    for key, value in payload.values.items():
        existing = repo.get_by_key(key, profile=payload.profile)
        if existing:
            # Check if editable
            if not existing.is_editable:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Setting key '{key}' is read-only."
                )
            repo.update(existing, {"value": str(value)})
            updated.append(existing)
        else:
            # Create a new general string setting if it doesn't exist
            new_setting = repo.upsert(key, str(value), profile=payload.profile)
            updated.append(new_setting)
    return updated

@router.get("/export", response_model=SettingsExport)
def export_settings(
    profile: str = Query("default"),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> SettingsExport:
    """Export all settings as a configuration snapshot."""
    repo = SettingRepository(session)
    settings_list = repo.list_for_profile(profile)
    
    # Cast to Schema list
    read_list = []
    for s in settings_list:
        read_list.append(
            SettingRead(
                id=s.id or 0,
                key=s.key,
                value=s.value,
                value_type=s.value_type,
                group=s.group,
                description=s.description,
                is_secret=s.is_secret,
                is_editable=s.is_editable,
                profile=s.profile,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
        )
        
    return SettingsExport(
        profile=profile,
        exported_at=datetime.now(timezone.utc),
        settings=read_list
    )

@router.post("/import", status_code=status.HTTP_204_NO_CONTENT)
def import_settings(
    payload: SettingsImport,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> None:
    """Import a settings configuration snapshot."""
    repo = SettingRepository(session)
    for s in payload.settings:
        existing = repo.get_by_key(s.key, profile=payload.profile)
        if existing and not payload.overwrite:
            continue
        repo.upsert(
            key=s.key,
            value=s.value,
            profile=payload.profile,
            value_type=s.value_type,
            group=s.group,
            description=s.description,
            is_secret=s.is_secret
        )
