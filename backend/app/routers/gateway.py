import json
from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from typing import Any, AsyncGenerator

from app.core.database import get_db
from app.core.exceptions import ProviderUnavailableError
from app.domain.enums import RoutingMode
from app.repositories.setting_repository import SettingRepository
from app.schemas.gateway import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    EmbeddingRequest,
    EmbeddingResponse,
    ImageGenerationRequest,
    ImageGenerationResponse
)
from app.services.gateway_service import GatewayService
from app.services.api_key_service import ApiKeyService
from app.repositories.provider_repository import ProviderRepository
from app.repositories.api_key_repository import ApiKeyRepository
from app.core.logging import get_logger

_logger = get_logger("gateway_router")
router = APIRouter()

def _resolve_routing_mode(x_routing_strategy: str | None, session: Session) -> RoutingMode:
    """Resolve routing mode from request header or fall back to database setting."""
    if x_routing_strategy:
        try:
            return RoutingMode(x_routing_strategy.lower())
        except ValueError:
            _logger.warning("gateway.invalid_routing_header", header_val=x_routing_strategy)
            
    setting_repo = SettingRepository(session)
    strategy_setting = setting_repo.get_by_key("routing_strategy")
    if strategy_setting and strategy_setting.value:
        try:
            return RoutingMode(strategy_setting.value.lower())
        except ValueError:
            pass
            
    return RoutingMode.PRIORITY

@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    x_routing_strategy: str | None = Header(default=None, alias="X-Routing-Strategy"),
    session: Session = Depends(get_db)
) -> Any:
    """Proxy OpenAI-compatible completions and stream requests with dynamic failover."""
    mode = _resolve_routing_mode(x_routing_strategy, session)
    gateway_service = GatewayService(session)
    
    if request.stream:
        async def stream_generator() -> AsyncGenerator[str, None]:
            try:
                generator = await gateway_service.execute_stream_chat(request, mode)
                async for chunk in generator:
                    yield f"data: {chunk.model_dump_json(exclude_none=True)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                _logger.error("gateway.stream_failed", error=str(e))
                # SSE format error block
                yield f"data: {json.dumps({'error': {'message': str(e), 'type': 'gateway_error'}})}\n\n"
                yield "data: [DONE]\n\n"
                
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
        
    try:
        return await gateway_service.execute_chat(request, mode)
    except ProviderUnavailableError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(
    request: EmbeddingRequest,
    session: Session = Depends(get_db)
) -> EmbeddingResponse:
    """Proxy embedding generation requests."""
    # Find candidates
    prov_repo = ProviderRepository(session)
    key_repo = ApiKeyRepository(session)
    api_key_service = ApiKeyService(session)
    
    # We will pick the first provider supporting embeddings
    from app.repositories.model_repository import ModelRepository
    model_repo = ModelRepository(session)
    models = [m for m in model_repo.list() if m.name == request.model and m.supports_embeddings and m.is_enabled]
    if not models:
        raise HTTPException(status_code=400, detail="No enabled model supports embeddings.")
        
    for m in models:
        provider = prov_repo.get(m.provider_id)
        if not provider or not provider.is_enabled:
            continue
        keys = [k for k in key_repo.list() if k.provider_id == provider.id and k.is_enabled]
        if not keys:
            continue
        # Use first key
        assert keys[0].id is not None
        raw_key = api_key_service.reveal_key(keys[0].id)
        plugin = api_key_service.plugin_manager.get_plugin(provider.plugin)
        try:
            return await plugin.create_embedding(raw_key, provider.base_url, request, provider.config)
        except Exception as e:
            _logger.error("gateway.embeddings.failed", provider=provider.name, error=str(e))
            continue
            
    raise HTTPException(status_code=503, detail="Embeddings service unavailable.")

@router.post("/images/generations", response_model=ImageGenerationResponse)
async def generate_images(
    request: ImageGenerationRequest,
    session: Session = Depends(get_db)
) -> ImageGenerationResponse:
    """Proxy image generation requests."""
    prov_repo = ProviderRepository(session)
    key_repo = ApiKeyRepository(session)
    api_key_service = ApiKeyService(session)
    
    # We will pick the first provider supporting image generation
    from app.repositories.model_repository import ModelRepository
    model_repo = ModelRepository(session)
    models = [m for m in model_repo.list() if m.supports_images and m.is_enabled]
    if not models:
        raise HTTPException(status_code=400, detail="No enabled model supports image generation.")
        
    for m in models:
        provider = prov_repo.get(m.provider_id)
        if not provider or not provider.is_enabled:
            continue
        keys = [k for k in key_repo.list() if k.provider_id == provider.id and k.is_enabled]
        if not keys:
            continue
        assert keys[0].id is not None
        raw_key = api_key_service.reveal_key(keys[0].id)
        plugin = api_key_service.plugin_manager.get_plugin(provider.plugin)
        try:
            return await plugin.generate_image(raw_key, provider.base_url, request, provider.config)
        except Exception as e:
            _logger.error("gateway.images.failed", provider=provider.name, error=str(e))
            continue
            
    raise HTTPException(status_code=503, detail="Image generation service unavailable.")
