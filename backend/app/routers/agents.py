from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Dict, Any

from app.services.agent_adapters.manager import AgentAdapterManager
from app.services.auth_service import require_role
from app.domain.entities.user import User
from app.domain.enums import UserRole
from app.core.database import get_db
from sqlmodel import Session
from app.repositories.setting_repository import SettingRepository

router = APIRouter()
manager = AgentAdapterManager()

class AgentWireRequest(BaseModel):
    base_url: str
    api_key: str
    model: str
    custom_path: str | None = None

class AgentRead(BaseModel):
    slug: str
    name: str
    config_path: str
    exists: bool

@router.get("", response_model=List[AgentRead])
def list_agents(
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> List[Dict[str, Any]]:
    """Retrieve all supported coding agents and their detection status."""
    adapters = manager.list_adapters()
    res = []
    for a in adapters:
        res.append({
            "slug": a.slug,
            "name": a.name,
            "config_path": a.get_config_path() or "",
            "exists": a.exists()
        })
    # Add custom agent template
    res.append({
        "slug": "custom",
        "name": "Custom Agent",
        "config_path": "",
        "exists": False
    })
    return res

@router.get("/{slug}/detect")
def detect_agent(
    slug: str,
    custom_path: str | None = Query(None),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Dict[str, Any]:
    """Detect configuration information for a specific agent."""
    try:
        adapter = manager.get_adapter(slug, custom_path or "")
        return adapter.detect()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{slug}/wire")
def wire_agent(
    slug: str,
    payload: AgentWireRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Dict[str, Any]:
    """Configure agent config parameters to route through AI Gateway Pro."""
    try:
        adapter = manager.get_adapter(slug, payload.custom_path or "")
        backup_path = adapter.backup()
        adapter.wire(payload.base_url, payload.api_key, payload.model)
        return {
            "success": True,
            "message": f"Successfully wired config for {adapter.name}",
            "backup_path": backup_path or "No backup created (config file was absent)."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{slug}/restore")
def restore_agent(
    slug: str,
    custom_path: str | None = Query(None),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Dict[str, Any]:
    """Restore the previous backup configuration for an agent."""
    try:
        adapter = manager.get_adapter(slug, custom_path or "")
        success = adapter.restore()
        if not success:
            raise HTTPException(status_code=400, detail="Failed to restore: No backup snapshot found.")
        return {"success": True, "message": "Successfully restored previous configuration."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/complete-setup")
def complete_setup(
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Dict[str, Any]:
    """Sets the setup wizard completed flag to true in settings."""
    repo = SettingRepository(session)
    repo.upsert("setup_wizard_completed", "true", group="general", value_type="boolean", description="Has the user finished setup wizard?")
    session.commit()
    return {"success": True}
