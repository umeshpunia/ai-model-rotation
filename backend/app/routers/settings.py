import os
import json
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
            
    session.commit()
    from app.services.config_hot_reload import trigger_config_hot_reload
    trigger_config_hot_reload()
    
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
        
    session.commit()
    from app.services.config_hot_reload import trigger_config_hot_reload
    trigger_config_hot_reload()

from pydantic import BaseModel

class ClaudeSettingsUpdate(BaseModel):
    api_key: str
    base_url: str
    model: str | None = None

@router.get("/claude")
def get_claude_settings(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    path = os.path.expanduser("~/.claude/settings.json")
    if not os.path.exists(path):
        return {"exists": False, "apiKey": "", "baseUrl": "", "model": ""}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        env = data.get("env", {})
        return {
            "exists": True,
            "apiKey": env.get("ANTHROPIC_API_KEY", ""),
            "baseUrl": env.get("ANTHROPIC_BASE_URL", ""),
            "model": data.get("model", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read Claude settings: {str(e)}")

@router.post("/claude")
def update_claude_settings(
    payload: ClaudeSettingsUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    path = os.path.expanduser("~/.claude/settings.json")
    backup_path = os.path.expanduser("~/.claude/settings.json.bak")
    
    # Check directory
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # Take backup if existing file exists
    if os.path.exists(path):
        try:
            import shutil
            shutil.copy2(path, backup_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create backup: {str(e)}")
            
    # Read current data or scaffold new
    data = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    if "env" not in data:
        data["env"] = {}
        
    data["env"]["ANTHROPIC_API_KEY"] = payload.api_key
    data["env"]["ANTHROPIC_BASE_URL"] = payload.base_url
    if payload.model:
        data["model"] = payload.model
    # Also update apiKeyHelper to match
    data["apiKeyHelper"] = f"echo '{payload.api_key}'"
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return {"success": True, "message": "Claude settings updated and backed up successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write Claude settings: {str(e)}")

@router.post("/claude/restore")
def restore_claude_settings(
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    path = os.path.expanduser("~/.claude/settings.json")
    backup_path = os.path.expanduser("~/.claude/settings.json.bak")
    
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=400, detail="No backup settings.json.bak file exists to restore.")
        
    try:
        import shutil
        shutil.copy2(backup_path, path)
        return {"success": True, "message": "Claude settings restored successfully from backup."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to restore backup: {str(e)}")
