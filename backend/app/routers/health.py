from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Any

from app.core.database import get_db
from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.enums import KeyStatus, ProviderStatus
from app.repositories.provider_repository import ProviderRepository
from app.repositories.api_key_repository import ApiKeyRepository

router = APIRouter()

@router.get("/health")
def health_check(session: Session = Depends(get_db)) -> dict[str, str]:
    """Basic health check verifying database connectivity."""
    try:
        # Check DB connection
        session.exec(select(1)).first()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )

@router.get("/status")
def status_overview(session: Session = Depends(get_db)) -> dict[str, Any]:
    """Breakdown of system configuration status (providers and key metrics)."""
    try:
        prov_repo = ProviderRepository(session)
        key_repo = ApiKeyRepository(session)
        
        providers = prov_repo.list()
        keys = key_repo.list()
        
        total_providers = len(providers)
        enabled_providers = sum(1 for p in providers if p.is_enabled)
        
        total_keys = len(keys)
        healthy_keys = sum(1 for k in keys if k.status == KeyStatus.HEALTHY)
        cooldown_keys = sum(1 for k in keys if k.status == KeyStatus.COOLDOWN)
        invalid_keys = sum(1 for k in keys if k.status == KeyStatus.INVALID)
        
        # Check setup_wizard_completed settings value
        from app.repositories.setting_repository import SettingRepository
        setting_repo = SettingRepository(session)
        wizard_setting = setting_repo.get_by_key("setup_wizard_completed")
        setup_wizard_completed = wizard_setting.value == "true" if wizard_setting else False
        
        return {
            "status": "online",
            "setup_wizard_completed": setup_wizard_completed,
            "providers": {
                "total": total_providers,
                "enabled": enabled_providers,
                "disabled": total_providers - enabled_providers
            },
            "api_keys": {
                "total": total_keys,
                "healthy": healthy_keys,
                "cooldown": cooldown_keys,
                "invalid": invalid_keys,
                "disabled": sum(1 for k in keys if not k.is_enabled)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status aggregation failed: {str(e)}"
        )
