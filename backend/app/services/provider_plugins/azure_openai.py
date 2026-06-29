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

class AzureOpenAIProviderPlugin(BaseProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "azure_openai"

    def _get_headers(self, api_key: str) -> Dict[str, str]:
        return {"api-key": api_key, "Content-Type": "application/json"}

    def _get_url(self, base_url: str, deployment: str, path: str, api_version: str) -> str:
        return f"{base_url}/openai/deployments/{deployment}/{path}?api-version={api_version}"

    async def test_connection(self, api_key: str, base_url: str, config: Dict[str, Any]) -> bool:
        deployment = config.get("deployment_name", "test")
        api_version = config.get("api_version", "2023-05-15")
        url = self._get_url(base_url, deployment, "chat/completions", api_version)
        payload = {"messages": [{"role": "user", "content": "ping"}], "max_tokens": 1}
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url, headers=self._get_headers(api_key), json=payload, timeout=10.0)
                return res.status_code == 200
            except Exception:
                return False

    async def chat_completion(
        self, api_key: str, base_url: str, request: ChatCompletionRequest, config: Dict[str, Any]
    ) -> ChatCompletionResponse:
        deployment = config.get("deployment_name", request.model)
        api_version = config.get("api_version", "2023-05-15")
        url = self._get_url(base_url, deployment, "chat/completions", api_version)
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=self._get_headers(api_key), json=request.model_dump(exclude_none=True))
            if res.status_code != 200:
                raise UpstreamError(f"Azure OpenAI error: {res.text}", status_code=res.status_code)
            return ChatCompletionResponse.model_validate(res.json())

    async def stream_chat_completion(
        self, api_key: str, base_url: str, request: ChatCompletionRequest, config: Dict[str, Any]
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        deployment = config.get("deployment_name", request.model)
        api_version = config.get("api_version", "2023-05-15")
        url = self._get_url(base_url, deployment, "chat/completions", api_version)
        request.stream = True
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, headers=self._get_headers(api_key), json=request.model_dump(exclude_none=True)) as response:
                if response.status_code != 200:
                    raise UpstreamError(f"Azure stream error: {await response.aread()}", status_code=response.status_code)
                async for line in response.aiter_lines():
                    line = line.strip()
                    if line.startswith("data: ") and line != "data: [DONE]":
                        yield ChatCompletionChunk.model_validate_json(line[6:])

    async def generate_image(
        self, api_key: str, base_url: str, request: ImageGenerationRequest, config: Dict[str, Any]
    ) -> ImageGenerationResponse:
        api_version = config.get("api_version", "2023-06-01-preview")
        url = f"{base_url}/openai/images/generations?api-version={api_version}"
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=self._get_headers(api_key), json=request.model_dump(exclude_none=True))
            if res.status_code != 200:
                raise UpstreamError(f"Azure Image error: {res.text}", status_code=res.status_code)
            return ImageGenerationResponse.model_validate(res.json())

    async def create_embedding(
        self, api_key: str, base_url: str, request: EmbeddingRequest, config: Dict[str, Any]
    ) -> EmbeddingResponse:
        deployment = config.get("deployment_name", request.model)
        api_version = config.get("api_version", "2023-05-15")
        url = self._get_url(base_url, deployment, "embeddings", api_version)
        async with httpx.AsyncClient() as client:
            res = await client.post(url, headers=self._get_headers(api_key), json=request.model_dump(exclude_none=True))
            if res.status_code != 200:
                raise UpstreamError(f"Azure Embedding error: {res.text}", status_code=res.status_code)
            return EmbeddingResponse.model_validate(res.json())
