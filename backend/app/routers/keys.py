from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import Any

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.domain.entities.api_key import ApiKey
from app.domain.entities.user import User
from app.domain.enums import UserRole
from app.repositories.api_key_repository import ApiKeyRepository
from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate, ApiKeyRead, ApiKeyReveal, ApiKeyTestResult
from app.services.api_key_service import ApiKeyService
from app.services.auth_service import require_role

router = APIRouter()

# Schema for key rotation request
from pydantic import BaseModel
class KeyRotateRequest(BaseModel):
    key: str

@router.get("", response_model=list[ApiKeyRead])
def list_keys(
    provider_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> list[ApiKey]:
    """Retrieve all configured API keys (optionally filtered by provider)."""
    repo = ApiKeyRepository(session)
    filters = {}
    if provider_id is not None:
        filters["provider_id"] = provider_id
    return repo.list(filters=filters, limit=limit, offset=skip)

@router.post("", response_model=ApiKeyRead, status_code=status.HTTP_201_CREATED)
def create_key(
    payload: ApiKeyCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> ApiKey:
    """Register a new API key."""
    service = ApiKeyService(session)
    try:
        return service.create_key(payload)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{id}", response_model=ApiKeyRead)
def get_key(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> ApiKey:
    """Get API key details by ID (secrets are masked)."""
    repo = ApiKeyRepository(session)
    key_model = repo.get(id)
    if not key_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with id {id} not found."
        )
    return key_model

@router.put("/{id}", response_model=ApiKeyRead)
def update_key(
    id: int,
    payload: ApiKeyUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> ApiKey:
    """Update API key configuration or replace secret."""
    service = ApiKeyService(session)
    try:
        return service.update_key(id, payload)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_key(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> None:
    """Delete an API key."""
    service = ApiKeyService(session)
    try:
        service.delete_key(id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/{id}/reveal", response_model=ApiKeyReveal)
def reveal_key(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> ApiKeyReveal:
    """Reveal the raw API key secret in plaintext (Admin only)."""
    service = ApiKeyService(session)
    try:
        raw_key = service.reveal_key(id)
        key_model = service.repo.get(id)
        assert key_model is not None
        return ApiKeyReveal(
            id=id,
            provider_id=key_model.provider_id,
            name=key_model.name,
            key=raw_key
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/{id}/test", response_model=ApiKeyTestResult)
async def test_key(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> ApiKeyTestResult:
    """Trigger a live validation test for an API key."""
    service = ApiKeyService(session)
    try:
        return await service.test_key(id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.post("/{id}/rotate", response_model=ApiKeyRead)
def rotate_key(
    id: int,
    payload: KeyRotateRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> ApiKey:
    """Rotate an API key with a new plaintext secret."""
    service = ApiKeyService(session)
    try:
        return service.update_key(id, ApiKeyUpdate(key=payload.key))
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
