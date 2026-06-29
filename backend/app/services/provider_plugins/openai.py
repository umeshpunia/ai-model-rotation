import httpx
from typing import AsyncGenerator, Dict, Any
from app.services.provider_plugins.base import BaseProviderPlugin
from app.schemas.gateway import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ImageGenerationRequest,
    ImageGenerationResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)
from app.core.exceptions import UpstreamError

class OpenAIProviderPlugin(BaseProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "openai"

    def _get_headers(self, api_key: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async def test_connection(self, api_key: str, base_url: str, config: Dict[str, Any]) -> bool:
        url = f"{base_url}/models"
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(url, headers=self._get_headers(api_key), timeout=10.0)
                return res.status_code == 200
            except Exception:
                return False

    async def chat_completion(
        self, api_key: str, base_url: str, request: ChatCompletionRequest, config: Dict[str, Any]
    ) -> ChatCompletionResponse:
        url = f"{base_url}/chat/completions"
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=self._get_headers(api_key), json=request.model_dump(exclude_none=True))
            if res.status_code != 200:
                raise UpstreamError(f"OpenAI error: {res.text}", status_code=res.status_code)
            return ChatCompletionResponse.model_validate(res.json())

    async def stream_chat_completion(
        self, api_key: str, base_url: str, request: ChatCompletionRequest, config: Dict[str, Any]
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        url = f"{base_url}/chat/completions"
        request.stream = True
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, headers=self._get_headers(api_key), json=request.model_dump(exclude_none=True)) as response:
                if response.status_code != 200:
                    raise UpstreamError(f"OpenAI stream error: {await response.aread()}", status_code=response.status_code)
                async for line in response.aiter_lines():
                    line = line.strip()
                    if line.startswith("data: ") and line != "data: [DONE]":
                        yield ChatCompletionChunk.model_validate_json(line[6:])

    async def generate_image(
        self, api_key: str, base_url: str, request: ImageGenerationRequest, config: Dict[str, Any]
    ) -> ImageGenerationResponse:
        url = f"{base_url}/images/generations"
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=self._get_headers(api_key), json=request.model_dump(exclude_none=True))
            if res.status_code != 200:
                raise UpstreamError(f"OpenAI Image error: {res.text}", status_code=res.status_code)
            return ImageGenerationResponse.model_validate(res.json())

    async def create_embedding(
        self, api_key: str, base_url: str, request: EmbeddingRequest, config: Dict[str, Any]
    ) -> EmbeddingResponse:
        url = f"{base_url}/embeddings"
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=self._get_headers(api_key), json=request.model_dump(exclude_none=True))
            if res.status_code != 200:
                raise UpstreamError(f"OpenAI Embedding error: {res.text}", status_code=res.status_code)
            return EmbeddingResponse.model_validate(res.json())
