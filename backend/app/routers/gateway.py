import json
import time
from fastapi import APIRouter, Depends, HTTPException, Header, status, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from typing import Any, AsyncGenerator, cast

from app.core.database import get_db
from app.core.exceptions import ProviderUnavailableError
from app.domain.enums import RoutingMode
from app.domain.entities.provider import Provider
from app.domain.entities.model import Model
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
                generator = gateway_service.execute_stream_chat(request, mode)
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

@router.post("/chat")
async def chat_legacy_alias(
    request: ChatCompletionRequest,
    x_routing_strategy: str | None = Header(default=None, alias="X-Routing-Strategy"),
    session: Session = Depends(get_db)
) -> Any:
    """Legacy/simple chat completions alias path."""
    request.stream = False
    return await chat_completions(request, x_routing_strategy, session)

@router.post("/stream")
async def chat_stream_legacy_alias(
    request: ChatCompletionRequest,
    x_routing_strategy: str | None = Header(default=None, alias="X-Routing-Strategy"),
    session: Session = Depends(get_db)
) -> Any:
    """Legacy/simple streaming chat completions alias path."""
    request.stream = True
    return await chat_completions(request, x_routing_strategy, session)

@router.post("/image", response_model=ImageGenerationResponse)
async def generate_images_legacy_alias(
    request: ImageGenerationRequest,
    session: Session = Depends(get_db)
) -> ImageGenerationResponse:
    """Legacy/simple image generation alias path."""
    return await generate_images(request, session)

@router.post("/embedding", response_model=EmbeddingResponse)
async def create_embeddings_legacy_alias(
    request: EmbeddingRequest,
    session: Session = Depends(get_db)
) -> EmbeddingResponse:
    """Legacy/simple embedding generation alias path."""
    return await create_embeddings(request, session)

@router.get("/providers", response_model=list[Any])
def list_gateway_providers(session: Session = Depends(get_db)) -> list[Any]:
    """List active providers under gateway namespace."""
    repo = ProviderRepository(session)
    return repo.list(order_by=cast(Any, Provider.priority).asc())

@router.get("/models", response_model=list[Any])
def list_gateway_models(session: Session = Depends(get_db)) -> list[Any]:
    """List configured models under gateway namespace."""
    from app.repositories.model_repository import ModelRepository
    repo = ModelRepository(session)
    return repo.list()

@router.get("/status")
def gateway_status(session: Session = Depends(get_db)) -> dict[str, Any]:
    """Get dynamic status of keys and providers under gateway namespace."""
    from app.domain.enums import KeyStatus
    prov_repo = ProviderRepository(session)
    key_repo = ApiKeyRepository(session)
    providers = prov_repo.list()
    keys = key_repo.list()
    return {
        "status": "online",
        "providers": {
            "total": len(providers),
            "enabled": sum(1 for p in providers if p.is_enabled)
        },
        "api_keys": {
            "total": len(keys),
            "healthy": sum(1 for k in keys if k.status == KeyStatus.HEALTHY),
            "cooldown": sum(1 for k in keys if k.status == KeyStatus.COOLDOWN),
            "invalid": sum(1 for k in keys if k.status == KeyStatus.INVALID),
            "disabled": sum(1 for k in keys if not k.is_enabled)
        }
    }

@router.get("/health")
def gateway_health(session: Session = Depends(get_db)) -> dict[str, str]:
    """Check connectivity and state under gateway namespace."""
    from sqlmodel import select
    try:
        session.exec(select(1)).first()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )

@router.get("/statistics", response_model=list[Any])
def gateway_statistics(session: Session = Depends(get_db)) -> list[Any]:
    """Get usage statistics under gateway namespace."""
    from app.repositories.statistic_repository import StatisticRepository
    repo = StatisticRepository(session)
    return repo.list()

from app.schemas.gateway import Message

@router.post("/messages")
async def anthropic_messages(
    request: Request,
    x_routing_strategy: str | None = Header(default=None, alias="X-Routing-Strategy"),
    session: Session = Depends(get_db)
) -> Any:
    """Proxy Anthropic-compatible messages and stream requests with dynamic failover translation."""
    body = await request.json()
    model_name = body.get("model")
    messages = body.get("messages", [])
    stream = body.get("stream", False)
    max_tokens = body.get("max_tokens", 4096)
    temperature = body.get("temperature", 1.0)
    system = body.get("system", None)
    
    # Map Anthropic request to internal ChatCompletionRequest
    internal_messages = []
    if system:
        internal_messages.append(Message(role="system", content=system))
        
    for msg in messages:
        role = msg.get("role")
        content = msg.get("content")
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            content_str = "\n".join(text_parts)
        else:
            content_str = str(content)
            
        internal_messages.append(Message(role=role, content=content_str))
        
    cc_request = ChatCompletionRequest(
        model=model_name,
        messages=internal_messages,
        temperature=temperature,
        stream=stream,
        max_tokens=max_tokens
    )
    
    mode = _resolve_routing_mode(x_routing_strategy, session)
    gateway_service = GatewayService(session)
    
    if stream:
        async def stream_generator() -> AsyncGenerator[str, None]:
            try:
                generator = gateway_service.execute_stream_chat(cc_request, mode)
                
                # 1. message_start event
                message_start = {
                    "type": "message_start",
                    "message": {
                        "id": "msg_stream_" + str(int(time.time())),
                        "type": "message",
                        "role": "assistant",
                        "content": [],
                        "model": model_name,
                        "stop_reason": None,
                        "stop_sequence": None,
                        "usage": {"input_tokens": 0, "output_tokens": 0}
                    }
                }
                yield f"event: message_start\ndata: {json.dumps(message_start)}\n\n"
                
                # 2. content_block_start event
                content_block_start = {
                    "type": "content_block_start",
                    "index": 0,
                    "content_block": {"type": "text", "text": ""}
                }
                yield f"event: content_block_start\ndata: {json.dumps(content_block_start)}\n\n"
                
                # 3. content deltas
                async for chunk in generator:
                    if chunk.choices and chunk.choices[0].delta.content:
                        delta_text = chunk.choices[0].delta.content
                        content_block_delta = {
                            "type": "content_block_delta",
                            "index": 0,
                            "delta": {"type": "text_delta", "text": delta_text}
                        }
                        yield f"event: content_block_delta\ndata: {json.dumps(content_block_delta)}\n\n"
                        
                # 4. content_block_stop
                content_block_stop = {
                    "type": "content_block_stop",
                    "index": 0
                }
                yield f"event: content_block_stop\ndata: {json.dumps(content_block_stop)}\n\n"
                
                # 5. message_delta
                message_delta = {
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                    "usage": {"output_tokens": 0}
                }
                yield f"event: message_delta\ndata: {json.dumps(message_delta)}\n\n"
                
                # 6. message_stop
                message_stop = {
                    "type": "message_stop"
                }
                yield f"event: message_stop\ndata: {json.dumps(message_stop)}\n\n"
                
            except Exception as e:
                _logger.error("gateway.anthropic_stream_failed", error=str(e))
                yield f"event: error\ndata: {json.dumps({'error': {'type': 'api_error', 'message': str(e)}})}\n\n"
                
        return StreamingResponse(stream_generator(), media_type="text/event-stream")
        
    try:
        res = await gateway_service.execute_chat(cc_request, mode)
        content_text = res.choices[0].message.content
        return {
            "id": res.id,
            "type": "message",
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": content_text
                }
            ],
            "model": res.model,
            "stop_reason": "end_turn" if res.choices[0].finish_reason != "length" else "max_tokens",
            "stop_sequence": None,
            "usage": {
                "input_tokens": res.usage.prompt_tokens,
                "output_tokens": res.usage.completion_tokens
            }
        }
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

