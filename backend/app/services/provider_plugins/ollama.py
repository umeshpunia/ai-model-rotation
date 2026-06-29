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
        # Test basic server tags status endpoint
        url = f"{base_url.rsplit('/v1', 1)[0]}/api/tags"
        async with httpx.AsyncClient() as client:
            try:
                res = await client.get(url, timeout=5.0)
                return res.status_code == 200
            except Exception:
                return False
