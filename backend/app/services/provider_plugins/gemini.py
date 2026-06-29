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
    EmbeddingData,
)
from app.core.exceptions import UpstreamError

class GeminiProviderPlugin(BaseProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "gemini"

    def _map_messages(self, messages):
        contents = []
        for msg in messages:
            role = "user" if msg.role in ("user", "system") else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })
        return contents

    async def test_connection(self, api_key: str, base_url: str, config: Dict[str, Any]) -> bool:
        url = f"{base_url}/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": "ping"}]}]}
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url, json=payload, timeout=10.0)
                return res.status_code == 200
            except Exception:
                return False

    async def chat_completion(
        self, api_key: str, base_url: str, request: ChatCompletionRequest, config: Dict[str, Any]
    ) -> ChatCompletionResponse:
        url = f"{base_url}/v1beta/models/{request.model}:generateContent?key={api_key}"
        payload = {
            "contents": self._map_messages(request.messages),
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            }
        }
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload)
            if res.status_code != 200:
                raise UpstreamError(f"Gemini error: {res.text}", status_code=res.status_code)
            
            data = res.json()
            try:
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError):
                text_out = ""

            return ChatCompletionResponse(
                id=f"gemini-{int(time.time())}",
                created=int(time.time()),
                model=request.model,
                choices=[ChatChoice(
                    index=0,
                    message=Message(role="assistant", content=text_out),
                    finish_reason="stop"
                )],
                usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
            )

    async def stream_chat_completion(
        self, api_key: str, base_url: str, request: ChatCompletionRequest, config: Dict[str, Any]
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        url = f"{base_url}/v1beta/models/{request.model}:streamGenerateContent?key={api_key}"
        payload = {
            "contents": self._map_messages(request.messages),
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            }
        }
        chunk_id = f"gemini-stream-{int(time.time())}"
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    raise UpstreamError(f"Gemini stream error: {await response.aread()}", status_code=response.status_code)
                import json
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("[") or line.startswith(","):
                        line = line[1:].strip()
                    if line.endswith("]"):
                        line = line[:-1].strip()
                    if not line:
                        continue
                    try:
                        chunk_data = json.loads(line)
                        text_part = chunk_data["candidates"][0]["content"]["parts"][0]["text"]
                        yield ChatCompletionChunk(
                            id=chunk_id,
                            created=int(time.time()),
                            model=request.model,
                            choices=[ChatChunkChoice(
                                index=0,
                                delta=Delta(role="assistant", content=text_part)
                            )]
                        )
                    except Exception:
                        pass

    async def generate_image(
        self, api_key: str, base_url: str, request: ImageGenerationRequest, config: Dict[str, Any]
    ) -> ImageGenerationResponse:
        raise NotImplementedError("Gemini plugin does not support image generation natively yet.")

    async def create_embedding(
        self, api_key: str, base_url: str, request: EmbeddingRequest, config: Dict[str, Any]
    ) -> EmbeddingResponse:
        url = f"{base_url}/v1beta/models/{request.model}:embedContent?key={api_key}"
        payload = {
            "content": {"parts": [{"text": request.input[0]}]}
        }
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload)
            if res.status_code != 200:
                raise UpstreamError(f"Gemini embedding error: {res.text}", status_code=res.status_code)
            data = res.json()
            vector = data["embedding"]["values"]
            return EmbeddingResponse(
                object="list",
                data=[EmbeddingData(embedding=vector, index=0)],
                model=request.model,
                usage={"prompt_tokens": 0, "total_tokens": 0}
            )
