from app.services.provider_plugins.openai import OpenAIProviderPlugin

class OpenRouterProviderPlugin(OpenAIProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "openrouter"
