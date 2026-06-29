# Design Specification: Phase 4 Provider Plugin System

## 1. Goal
Design and implement a dynamic, extensible, and robust provider plugin architecture for the AI Gateway Pro backend. The gateway must dynamically discover provider plugins from the `provider_plugins/` folder, implement specific client translations for supported providers (OpenAI, Gemini, Anthropic, DeepSeek, Grok, OpenRouter, Ollama, Azure OpenAI) using async networking (`httpx`), and support provider configuration import/export.

## 2. Requirements & Scope
- **Plugin Architecture**:
  - `BaseProviderPlugin` abstract base class defining common operations: test connection, chat completion, streaming, image generation, and text embeddings.
  - `PluginManager` to discover, dynamically load, register, and serve plugin instances at runtime.
- **Provider Implementations**:
  - **OpenAI-Compatible formats**: OpenAI, DeepSeek, Grok, OpenRouter, Ollama, and Azure OpenAI.
  - **Native translation formats**: Anthropic (Claude) and Gemini.
- **Provider Connection Testing**: Minimal API checks to verify token validity and network routing.
- **Import/Export Utility**: Functions in `ProviderService` to import and export list/individual configurations as JSON.

## 3. Design Details

### A. DTO Schemas for Gateway Communication (`schemas/gateway.py`)
To isolate client payloads, we will define OpenAI-compatible Pydantic models for chat request, response, chunks (streaming), image generation, and text embeddings.

### B. Abstract Base Class (`services/provider_plugins/base.py`)
- Define `BaseProviderPlugin(ABC)`.
- Specify methods:
  - `async def test_connection(...) -> bool`
  - `async def chat_completion(...) -> ChatCompletionResponse`
  - `async def stream_chat_completion(...) -> AsyncGenerator[ChatCompletionChunk, None]`
  - `async def generate_image(...) -> ImageGenerationResponse`
  - `async def create_embedding(...) -> EmbeddingResponse`

### C. Plugin Manager (`services/provider_plugins/manager.py`)
- Maintains a registry: `_plugins: dict[str, BaseProviderPlugin]`.
- Scans `app/services/provider_plugins/` directory for Python modules (excluding `__init__.py` and `base.py`).
- Inspects subclasses of `BaseProviderPlugin` and instantiates them.
- Exposes `get_plugin(slug: str) -> BaseProviderPlugin`.

### D. Provider Implementations
- **OpenAI / DeepSeek / Grok / OpenRouter / Ollama / Azure OpenAI**: Send JSON payloads straight to their respective `/chat/completions` or `/embeddings` endpoints. We wrap headers and API keys.
- **Gemini**: Maps `messages` to `contents` and `parts`. Connects to `/v1beta/models/{model}:generateContent` and parses candidate text parts back to chat completion shape.
- **Anthropic**: Maps `messages` to Anthropic's message structure. Connects to `/v1/messages` and parses blocks back to standard choice text.

### E. Import / Export and Connection Testing (`services/provider_service.py`)
- `ProviderService` delegating connection tests to plugins.
- Serializes `Provider` DB models to JSON list formats for exports, and parses them back for imports.

## 4. Verification Plan
- **Unit Tests**:
  - Verify `PluginManager` discovers and registers stubs.
  - Verify payload mapper translates OpenAI request structure to Gemini and Anthropic structures.
  - Verify connection test calls return correct results.
- **Integration Tests**: Mock external provider API calls using `pytest-mock` or `httpx.MockTransport` and verify end-to-end routing integration.
