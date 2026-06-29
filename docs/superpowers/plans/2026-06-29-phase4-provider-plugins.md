# Phase 4 Provider Plugin System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Design and implement the provider plugin interface, runtime plugin manager, specific provider clients (OpenAI, Gemini, Anthropic, etc.), connection testing, import/export logic, and unit tests.

**Architecture:** Create gateway communication DTO schemas, define the BaseProviderPlugin abstract class, implement runtime plugin discovery, write translation-based clients using httpx, and add import/export services.

**Tech Stack:** Python 3.12, httpx (async), pydantic

---

### Task 1: Create Gateway DTO Schemas

**Files:**
- Create: `backend/app/schemas/gateway.py`

- [ ] **Step 1: Write gateway DTO schemas**

Write the following code into `backend/app/schemas/gateway.py`:
```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    user: Optional[str] = None

class ChatChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Usage

class Delta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None

class ChatChunkChoice(BaseModel):
    index: int
    delta: Delta
    finish_reason: Optional[str] = None

class ChatCompletionChunk(BaseModel):
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatChunkChoice]

class ImageGenerationRequest(BaseModel):
    prompt: str
    n: Optional[int] = 1
    size: Optional[str] = "1024x1024"
    response_format: Optional[str] = "url"
    user: Optional[str] = None

class ImageData(BaseModel):
    url: Optional[str] = None
    b64_json: Optional[str] = None
    revised_prompt: Optional[str] = None

class ImageGenerationResponse(BaseModel):
    created: int
    data: List[ImageData]

class EmbeddingRequest(BaseModel):
    input: List[str]
    model: str
    encoding_format: Optional[str] = "float"
    user: Optional[str] = None

class EmbeddingData(BaseModel):
    object: str = "embedding"
    embedding: List[float]
    index: int

class EmbeddingResponse(BaseModel):
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: Dict[str, int]
```

- [ ] **Step 2: Commit DTO schemas**

Run:
```bash
git add backend/app/schemas/gateway.py
git commit -m "feat(gateway): add OpenAI-compatible gateway request/response DTO schemas"
```

---

### Task 2: Create Abstract Base Class and Plugin Manager

**Files:**
- Create: `backend/app/services/provider_plugins/base.py`
- Create: `backend/app/services/provider_plugins/manager.py`

- [ ] **Step 1: Write BaseProviderPlugin interface**

Write the following code into `backend/app/services/provider_plugins/base.py`:
```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Dict
from app.schemas.gateway import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChunk,
    ImageGenerationRequest,
    ImageGenerationResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)

class BaseProviderPlugin(ABC):
    """Abstract base class for all provider plugins."""

    @property
    @abstractmethod
    def provider_slug(self) -> str:
        """Slug identifying the provider (e.g. 'openai')."""
        pass

    @abstractmethod
    async def test_connection(self, api_key: str, base_url: str, config: Dict[str, Any]) -> bool:
        """Test API credentials."""
        pass

    @abstractmethod
    async def chat_completion(
        self, api_key: str, base_url: str, request: ChatCompletionRequest, config: Dict[str, Any]
    ) -> ChatCompletionResponse:
        """Run non-streaming chat request."""
        pass

    @abstractmethod
    async def stream_chat_completion(
        self, api_key: str, base_url: str, request: ChatCompletionRequest, config: Dict[str, Any]
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        """Run streaming chat request."""
        pass

    @abstractmethod
    async def generate_image(
        self, api_key: str, base_url: str, request: ImageGenerationRequest, config: Dict[str, Any]
    ) -> ImageGenerationResponse:
        """Run image generation request."""
        pass

    @abstractmethod
    async def create_embedding(
        self, api_key: str, base_url: str, request: EmbeddingRequest, config: Dict[str, Any]
    ) -> EmbeddingResponse:
        """Run text embedding request."""
        pass
```

- [ ] **Step 2: Write PluginManager discovery engine**

Write the following code into `backend/app/services/provider_plugins/manager.py`:
```python
import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, Type
from app.services.provider_plugins.base import BaseProviderPlugin
from app.core.logging import get_logger

_logger = get_logger("app")

class PluginManager:
    """Discovers, loads, and registers provider plugins dynamically."""

    def __init__(self, plugin_dir: str | None = None) -> None:
        from app.core.config import get_settings
        p_dir = plugin_dir or get_settings().provider.plugin_directory
        self.plugin_dir = Path(p_dir).resolve()
        self._plugins: Dict[str, BaseProviderPlugin] = {}

    def discover_plugins(self) -> None:
        """Scan directory and import all modules inheriting from BaseProviderPlugin."""
        if not self.plugin_dir.exists():
            _logger.warning("plugins.directory.missing", path=str(self.plugin_dir))
            return
        
        for file in self.plugin_dir.glob("*.py"):
            if file.name in ("__init__.py", "base.py", "manager.py"):
                continue
            module_name = f"app.services.provider_plugins.{file.stem}"
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, BaseProviderPlugin)
                        and attr is not BaseProviderPlugin
                    ):
                        plugin_inst = attr()
                        self._plugins[plugin_inst.provider_slug] = plugin_inst
                        _logger.info("plugin.registered", slug=plugin_inst.provider_slug)
            except Exception as e:
                _logger.error("plugin.import.failed", module=module_name, error=str(e))

    def get_plugin(self, slug: str) -> BaseProviderPlugin:
        if not self._plugins:
            self.discover_plugins()
        if slug not in self._plugins:
            raise KeyError(f"No provider plugin registered for slug: {slug}")
        return self._plugins[slug]

_manager = PluginManager()

def get_plugin_manager() -> PluginManager:
    return _manager
```

- [ ] **Step 3: Update `provider_plugins/__init__.py` to export helpers**

Update `backend/app/services/provider_plugins/__init__.py`:
```python
from app.services.provider_plugins.base import BaseProviderPlugin
from app.services.provider_plugins.manager import get_plugin_manager, PluginManager

__all__ = ["BaseProviderPlugin", "get_plugin_manager", "PluginManager"]
```

- [ ] **Step 4: Commit plugin foundation**

Run:
```bash
git add backend/app/services/provider_plugins/base.py backend/app/services/provider_plugins/manager.py backend/app/services/provider_plugins/__init__.py
git commit -m "feat(plugins): implement abstract plugin class and dynamic PluginManager"
```

---

### Task 3: Implement OpenAI, DeepSeek, Grok, OpenRouter, Ollama, and Azure OpenAI Plugins

**Files:**
- Create: `backend/app/services/provider_plugins/openai.py`
- Create: `backend/app/services/provider_plugins/deepseek.py`
- Create: `backend/app/services/provider_plugins/grok.py`
- Create: `backend/app/services/provider_plugins/openrouter.py`
- Create: `backend/app/services/provider_plugins/ollama.py`
- Create: `backend/app/services/provider_plugins/azure_openai.py`

- [ ] **Step 1: Write OpenAI plugin (base for compatibility)**

Write the following code into `backend/app/services/provider_plugins/openai.py`:
```python
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
```

- [ ] **Step 2: Write DeepSeek plugin**

Write the following code into `backend/app/services/provider_plugins/deepseek.py`:
```python
from app.services.provider_plugins.openai import OpenAIProviderPlugin

class DeepSeekProviderPlugin(OpenAIProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "deepseek"
```

- [ ] **Step 3: Write Grok plugin**

Write the following code into `backend/app/services/provider_plugins/grok.py`:
```python
from app.services.provider_plugins.openai import OpenAIProviderPlugin

class GrokProviderPlugin(OpenAIProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "grok"
```

- [ ] **Step 4: Write OpenRouter plugin**

Write the following code into `backend/app/services/provider_plugins/openrouter.py`:
```python
from app.services.provider_plugins.openai import OpenAIProviderPlugin

class OpenRouterProviderPlugin(OpenAIProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "openrouter"
```

- [ ] **Step 5: Write Ollama plugin**

Write the following code into `backend/app/services/provider_plugins/ollama.py`:
```python
import httpx
from typing import Dict, Any
from app.services.provider_plugins.openai import OpenAIProviderPlugin

class OllamaProviderPlugin(OpenAIProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "ollama"

    def _get_headers(self, api_key: str) -> Dict[str, str]:
        return {"Content-Type": "application/json"}

    async def test_connection(self, api_key: str, base_url: str, config: Dict[str, Any]) -> bool:
        # Test basic server status
        url = f"{base_url.rsplit('/v1', 1)[0]}/api/tags"
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(url, timeout=5.0)
                return res.status_code == 200
            except Exception:
                return False
```

- [ ] **Step 6: Write Azure OpenAI plugin**

Write the following code into `backend/app/services/provider_plugins/azure_openai.py`:
```python
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
        # Azure OpenAI image generation usually goes to the non-deployment specific path
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
```

- [ ] **Step 7: Commit OpenAI compatibility family plugins**

Run:
```bash
git add backend/app/services/provider_plugins/openai.py backend/app/services/provider_plugins/deepseek.py backend/app/services/provider_plugins/grok.py backend/app/services/provider_plugins/openrouter.py backend/app/services/provider_plugins/ollama.py backend/app/services/provider_plugins/azure_openai.py
git commit -m "feat(plugins): implement compatible format plugins (OpenAI, DeepSeek, Grok, OpenRouter, Ollama, Azure)"
```

---

### Task 4: Implement Gemini and Anthropic Plugins

**Files:**
- Create: `backend/app/services/provider_plugins/gemini.py`
- Create: `backend/app/services/provider_plugins/anthropic.py`

- [ ] **Step 1: Write Gemini plugin (maps OpenAI request format to Google format)**

Write the following code into `backend/app/services/provider_plugins/gemini.py`:
```python
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
        # Use gemini-1.5-flash or default model to test
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
                # Parse json stream
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
        # Maps to embedContent endpoint
        # Gemini embedding requests expect models like text-embedding-004
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
```

- [ ] **Step 2: Write Anthropic plugin (maps to Anthropic Messages API)**

Write the following code into `backend/app/services/provider_plugins/anthropic.py`:
```python
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
            # Anthropic does not support 'system' in messages list natively (it goes as a top-level param)
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
```

- [ ] **Step 3: Commit Gemini and Anthropic translation plugins**

Run:
```bash
git add backend/app/services/provider_plugins/gemini.py backend/app/services/provider_plugins/anthropic.py
git commit -m "feat(plugins): implement native translation plugins (Gemini and Anthropic)"
```

---

### Task 5: Implement Provider Service, Connection Testing, and Import/Export

**Files:**
- Create: `backend/app/services/provider_service.py`

- [ ] **Step 1: Write ProviderService class**

Write the following code into `backend/app/services/provider_service.py`:
```python
import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.domain.entities.provider import Provider
from app.repositories.provider_repository import ProviderRepository
from app.repositories.api_key_repository import ApiKeyRepository
from app.schemas.provider import ProviderCreate, ProviderUpdate
from app.services.provider_plugins.manager import get_plugin_manager
from app.core.exceptions import NotFoundError, ValidationError

class ProviderService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = ProviderRepository(session)
        self.key_repo = ApiKeyRepository(session)
        self.plugin_manager = get_plugin_manager()

    async def test_provider_connection(self, provider_id: int, api_key: str) -> bool:
        provider = self.repo.get_or_404(provider_id)
        plugin = self.plugin_manager.get_plugin(provider.plugin)
        return await plugin.test_connection(api_key, provider.base_url, provider.config)

    def export_providers(self) -> str:
        """Export all configured providers (excluding credentials) as JSON."""
        providers = self.repo.list()
        export_data = []
        for p in providers:
            export_data.append({
                "name": p.name,
                "slug": p.slug,
                "description": p.description,
                "plugin": p.plugin,
                "api_format": p.api_format.value,
                "auth_type": p.auth_type.value,
                "base_url": p.base_url,
                "default_model": p.default_model,
                "priority": p.priority,
                "config": p.config,
                "extra_headers": p.extra_headers,
                "is_enabled": p.is_enabled,
            })
        return json.dumps(export_data, indent=2)

    def import_providers(self, json_data: str) -> List[Provider]:
        """Import provider configurations from JSON."""
        try:
            items = json.loads(json_data)
        except Exception as e:
            raise ValidationError(f"Invalid JSON format: {e}")
        
        imported = []
        for item in items:
            # Check if provider already exists by slug
            slug = item.get("slug")
            if not slug:
                raise ValidationError("Missing slug in provider configuration.")
            
            existing = self.repo.get_by(slug=slug)
            if existing:
                # Update existing provider
                self.repo.update(existing, item)
                imported.append(existing)
            else:
                # Create new
                provider = Provider(**item)
                self.repo.add(provider)
                imported.append(provider)
        return imported
```

- [ ] **Step 2: Commit ProviderService**

Run:
```bash
git add backend/app/services/provider_service.py
git commit -m "feat(services): implement ProviderService connection testing and configuration import/export"
```

---

### Task 6: Create Unit & Integration Tests

**Files:**
- Create: `backend/tests/unit/test_plugins.py`

- [ ] **Step 1: Write tests for dynamic discovery, translations, and connection tests**

Write the following code into `backend/tests/unit/test_plugins.py`:
```python
import pytest
from app.services.provider_plugins import get_plugin_manager
from app.services.provider_plugins.base import BaseProviderPlugin
from app.schemas.gateway import ChatCompletionRequest, Message
from app.domain.enums import ApiFormat, AuthType
from app.services.provider_service import ProviderService
from app.repositories.provider_repository import ProviderRepository
from app.domain.entities.provider import Provider
from app.core.database import session_scope, get_settings, dispose_engine

@pytest.fixture(autouse=True)
def setup_test_db():
    settings = get_settings()
    original_url = settings.database.database_test_url
    settings.database.database_test_url = "sqlite:///:memory:"
    dispose_engine()
    
    from sqlmodel import SQLModel
    from app.core.database import get_engine
    SQLModel.metadata.create_all(get_engine())
    yield
    SQLModel.metadata.drop_all(get_engine())
    settings.database.database_test_url = original_url
    dispose_engine()

def test_plugin_discovery():
    mgr = get_plugin_manager()
    mgr.discover_plugins()
    
    openai_plugin = mgr.get_plugin("openai")
    assert isinstance(openai_plugin, BaseProviderPlugin)
    assert openai_plugin.provider_slug == "openai"
    
    gemini_plugin = mgr.get_plugin("gemini")
    assert gemini_plugin.provider_slug == "gemini"

def test_gemini_message_mapping():
    mgr = get_plugin_manager()
    gemini = mgr.get_plugin("gemini")
    
    req = ChatCompletionRequest(
        model="gemini-1.5-flash",
        messages=[
            Message(role="system", content="sys-prompt"),
            Message(role="user", content="hello"),
            Message(role="assistant", content="response"),
        ]
    )
    mapped = gemini._map_messages(req.messages)
    assert len(mapped) == 3
    assert mapped[0]["role"] == "user"  # system mapped to user
    assert mapped[0]["parts"][0]["text"] == "sys-prompt"
    assert mapped[1]["role"] == "user"
    assert mapped[2]["role"] == "model"

def test_anthropic_message_mapping():
    mgr = get_plugin_manager()
    anthropic = mgr.get_plugin("anthropic")
    
    req = ChatCompletionRequest(
        model="claude-3-haiku",
        messages=[
            Message(role="system", content="sys-prompt"),
            Message(role="user", content="hello"),
        ]
    )
    mapped = anthropic._map_messages(req.messages)
    assert len(mapped) == 1
    assert mapped[0]["role"] == "user"
    assert mapped[0]["content"] == "hello"
    
    sys_msg = anthropic._get_system_message(req.messages)
    assert sys_msg == "sys-prompt"

def test_provider_service_import_export():
    with session_scope() as session:
        service = ProviderService(session)
        
        provider = Provider(
            name="OpenAI Provider",
            slug="openai",
            plugin="openai",
            api_format=ApiFormat.OPENAI,
            auth_type=AuthType.BEARER,
            base_url="https://api.openai.com/v1"
        )
        service.repo.add(provider)
        
        exported = service.export_providers()
        assert "openai" in exported
        
        # Test Import
        imported = service.import_providers(exported)
        assert len(imported) == 1
        assert imported[0].slug == "openai"
```

- [ ] **Step 2: Run all tests**

Run: `.venv\Scripts\pytest tests/ -v`
Expected output: 25 passed tests.

- [ ] **Step 3: Commit plugin tests**

Run:
```bash
git add backend/tests/unit/test_plugins.py
git commit -m "test: add provider plugin discovery, message translation, and configuration service tests"
```

---

### Task 7: Update Phase Status Documentation

**Files:**
- Modify: `phase.md`

- [ ] **Step 1: Check off Phase 4 checkboxes**

Edit `d:\projects\python\ai-model-rotation\phase.md` lines 86-102.
Change all checkboxes under `## Phase 4: Provider Plugin System` to `[x]`.

- [ ] **Step 2: Update Phase 4 summary status**

Edit `d:\projects\python\ai-model-rotation\phase.md` line 354.
Change:
```markdown
| 4 | Provider Plugin System | Not Started |
```
To:
```markdown
| 4 | Provider Plugin System | Complete |
```

- [ ] **Step 3: Commit phase documentation updates**

Run:
```bash
git add phase.md docs/superpowers/plans/2026-06-29-phase4-provider-plugins.md docs/superpowers/specs/2026-06-29-phase4-provider-plugins-design.md
git commit -m "docs: complete Phase 4 provider plugin system status tracking and specs/plans"
```
Expected output: Commit completed.
