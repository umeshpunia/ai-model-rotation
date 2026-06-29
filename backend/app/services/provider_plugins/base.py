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
