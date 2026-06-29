import time
from typing import Any, cast
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.entities.provider import Provider
from app.domain.entities.user import User
from app.domain.enums import UserRole
from app.repositories.provider_repository import ProviderRepository
from app.repositories.api_key_repository import ApiKeyRepository
from app.schemas.provider import ProviderCreate, ProviderUpdate, ProviderRead, ProviderTestResult
from app.services.provider_service import ProviderService
from app.services.api_key_service import ApiKeyService
from app.services.auth_service import require_role

router = APIRouter()

# Schema for connection test payload
from pydantic import BaseModel
class ProviderTestRequest(BaseModel):
    api_key: str | None = None

@router.get("", response_model=list[ProviderRead])
def list_providers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> list[Provider]:
    """Retrieve all configured providers with pagination."""
    repo = ProviderRepository(session)
    # Order by priority
    return repo.list(order_by=cast(Any, Provider.priority).asc(), limit=limit, offset=skip)

@router.post("", response_model=ProviderRead, status_code=status.HTTP_201_CREATED)
def create_provider(
    payload: ProviderCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Provider:
    """Create a new provider configuration."""
    repo = ProviderRepository(session)
    
    # Auto-slugify name if slug not provided
    slug = payload.slug
    if not slug:
        from app.schemas.provider import _slugify
        slug = _slugify(payload.name)
        
    # Check duplicate slug
    if repo.get_by(slug=slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Provider with slug '{slug}' already exists."
        )
        
    provider = Provider(
        name=payload.name,
        slug=slug,
        description=payload.description,
        plugin=payload.plugin,
        api_format=payload.api_format,
        auth_type=payload.auth_type,
        base_url=payload.base_url,
        default_model=payload.default_model,
        priority=payload.priority,
        timeout_seconds=payload.timeout_seconds,
        max_retries=payload.max_retries,
        config=payload.config,
        extra_headers=payload.extra_headers,
        is_enabled=payload.is_enabled,
        status=payload.status
    )
    repo.add(provider)
    return provider

@router.get("/{id}", response_model=ProviderRead)
def get_provider(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Provider:
    """Get provider details by ID."""
    repo = ProviderRepository(session)
    provider = repo.get(id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider with id {id} not found."
        )
    return provider

@router.put("/{id}", response_model=ProviderRead)
def update_provider(
    id: int,
    payload: ProviderUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Provider:
    """Update a provider configuration."""
    repo = ProviderRepository(session)
    provider = repo.get(id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider with id {id} not found."
        )
        
    # Filter none values to partial update
    update_data = payload.model_dump(exclude_unset=True)
    repo.update(provider, update_data)
    return provider

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> None:
    """Delete a provider configuration."""
    repo = ProviderRepository(session)
    provider = repo.get(id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider with id {id} not found."
        )
    repo.delete(provider)

@router.post("/{id}/test", response_model=ProviderTestResult)
async def test_provider(
    id: int,
    payload: ProviderTestRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> ProviderTestResult:
    """Test connection for a provider configuration."""
    provider_service = ProviderService(session)
    api_key_service = ApiKeyService(session)
    
    # Retrieve raw key
    raw_key = payload.api_key
    if not raw_key:
        # Fall back to highest priority enabled key associated with provider
        key_repo = ApiKeyRepository(session)
        keys = [k for k in key_repo.list() if k.provider_id == id and k.is_enabled]
        keys.sort(key=lambda k: k.priority)
        if not keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active API keys configured for this provider. Please provide an api_key in payload."
            )
        # Reveal key
        assert keys[0].id is not None
        raw_key = api_key_service.reveal_key(keys[0].id)
        
    start_time = time.perf_counter()
    try:
        success = await provider_service.test_provider_connection(id, raw_key)
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return ProviderTestResult(
            provider_id=id,
            success=success,
            latency_ms=latency_ms,
            status_code=200 if success else 400,
            message="Connection test succeeded" if success else "Connection test failed"
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return ProviderTestResult(
            provider_id=id,
            success=False,
            latency_ms=latency_ms,
            status_code=500,
            message=str(e)
        )
