import httpx
import time
from typing import AsyncGenerator, Dict, Any
from app.services.provider_plugins.base import BaseProviderPlugin
from app.schemas.gateway import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatChoice,
    Message,
    Usage,
    ChatCompletionChunk,
    ChatChunkChoice,
    Delta,
    ImageGenerationRequest,
    ImageGenerationResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)
from app.core.exceptions import UpstreamError

class AnthropicProviderPlugin(BaseProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "anthropic"

    def _get_headers(self, api_key: str) -> Dict[str, str]:
        return {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

    def _map_messages(self, messages):
        mapped = []
        for msg in messages:
            if msg.role == "system":
                continue
            mapped.append({"role": msg.role, "content": msg.content})
        return mapped

    def _get_system_message(self, messages) -> str | None:
        for msg in messages:
            if msg.role == "system":
                return msg.content
        return None

    async def test_connection(self, api_key: str, base_url: str, config: Dict[str, Any]) -> bool:
        url = f"{base_url}/v1/messages"
        payload = {
            "model": "claude-3-haiku-20240307",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1
        }
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url, headers=self._get_headers(api_key), json=payload, timeout=10.0)
                return res.status_code == 200
            except Exception:
                return False

    async def chat_completion(
        self, api_key: str, base_url: str, request: ChatCompletionRequest, config: Dict[str, Any]
    ) -> ChatCompletionResponse:
        url = f"{base_url}/v1/messages"
        payload = {
            "model": request.model,
            "messages": self._map_messages(request.messages),
            "max_tokens": request.max_tokens or 1024,
            "temperature": request.temperature,
        }
        sys_msg = self._get_system_message(request.messages)
        if sys_msg:
            payload["system"] = sys_msg

        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=self._get_headers(api_key), json=payload)
            if res.status_code != 200:
                raise UpstreamError(f"Anthropic error: {res.text}", status_code=res.status_code)
            data = res.json()
            text_out = data["content"][0]["text"]
            input_tokens = data["usage"]["input_tokens"]
            output_tokens = data["usage"]["output_tokens"]
            
            return ChatCompletionResponse(
                id=data["id"],
                created=int(time.time()),
                model=request.model,
                choices=[ChatChoice(
                    index=0,
                    message=Message(role="assistant", content=text_out),
                    finish_reason=data.get("stop_reason", "stop")
                )],
                usage=Usage(
                    prompt_tokens=input_tokens,
                    completion_tokens=output_tokens,
                    total_tokens=input_tokens + output_tokens
                )
            )

    async def stream_chat_completion(
        self, api_key: str, base_url: str, request: ChatCompletionRequest, config: Dict[str, Any]
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        url = f"{base_url}/v1/messages"
        payload = {
            "model": request.model,
            "messages": self._map_messages(request.messages),
            "max_tokens": request.max_tokens or 1024,
            "temperature": request.temperature,
            "stream": True,
        }
        sys_msg = self._get_system_message(request.messages)
        if sys_msg:
            payload["system"] = sys_msg

        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, headers=self._get_headers(api_key), json=payload) as response:
                if response.status_code != 200:
                    raise UpstreamError(f"Anthropic stream error: {await response.aread()}", status_code=response.status_code)
                import json
                async for line in response.aiter_lines():
                    line = line.strip()
                    if line.startswith("data:"):
                        try:
                            event_data = json.loads(line[5:].strip())
                            e_type = event_data.get("type")
                            if e_type == "content_block_delta":
                                delta_text = event_data["delta"]["text"]
                                yield ChatCompletionChunk(
                                    id="anthropic-chunk",
                                    created=int(time.time()),
                                    model=request.model,
                                    choices=[ChatChunkChoice(
                                        index=0,
                                        delta=Delta(role="assistant", content=delta_text)
                                    )]
                                )
                        except Exception:
                            pass

    async def generate_image(
        self, api_key: str, base_url: str, request: ImageGenerationRequest, config: Dict[str, Any]
    ) -> ImageGenerationResponse:
        raise NotImplementedError("Anthropic does not support image generation.")

    async def create_embedding(
        self, api_key: str, base_url: str, request: EmbeddingRequest, config: Dict[str, Any]
    ) -> EmbeddingResponse:
        raise NotImplementedError("Anthropic does not support text embeddings.")
