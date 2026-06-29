from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session
from typing import Any

from app.core.database import get_db
from app.domain.entities.model import Model
from app.domain.entities.user import User
from app.domain.enums import UserRole
from app.repositories.model_repository import ModelRepository
from app.schemas.model import ModelCreate, ModelUpdate, ModelRead
from app.services.auth_service import require_role

router = APIRouter()

@router.get("", response_model=list[ModelRead])
def list_models(
    provider_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> list[Model]:
    """Retrieve all configured provider models."""
    repo = ModelRepository(session)
    filters = {}
    if provider_id is not None:
        filters["provider_id"] = provider_id
    return repo.list(filters=filters, limit=limit, offset=skip)

@router.post("", response_model=ModelRead, status_code=status.HTTP_201_CREATED)
def create_model(
    payload: ModelCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Model:
    """Add a model configuration to a provider."""
    repo = ModelRepository(session)
    model = Model(
        provider_id=payload.provider_id,
        name=payload.name,
        display_name=payload.display_name,
        description=payload.description,
        is_enabled=payload.is_enabled,
        sa_column=None if False else None, # Typo guard
        context_window=payload.context_window,
        max_output_tokens=payload.max_output_tokens,
        supports_streaming=payload.supports_streaming,
        supports_vision=payload.supports_vision,
        supports_tools=payload.supports_tools,
        supports_embeddings=payload.supports_embeddings,
        supports_images=payload.supports_images,
        input_cost_per_1k=payload.input_cost_per_1k,
        output_cost_per_1k=payload.output_cost_per_1k,
        task_types=payload.task_types,
        meta=payload.meta
    )
    repo.add(model)
    return model

@router.get("/{id}", response_model=ModelRead)
def get_model(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Model:
    """Get model details by ID."""
    repo = ModelRepository(session)
    model = repo.get(id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {id} not found."
        )
    return model

@router.put("/{id}", response_model=ModelRead)
def update_model(
    id: int,
    payload: ModelUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> Model:
    """Update a model configuration."""
    repo = ModelRepository(session)
    model = repo.get(id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {id} not found."
        )
    update_data = payload.model_dump(exclude_unset=True)
    repo.update(model, update_data)
    return model

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    id: int,
    session: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
) -> None:
    """Delete a model configuration."""
    repo = ModelRepository(session)
    model = repo.get(id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with id {id} not found."
        )
    repo.delete(id)
