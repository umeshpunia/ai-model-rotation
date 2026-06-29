from app.services.provider_plugins.openai import OpenAIProviderPlugin

class GrokProviderPlugin(OpenAIProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "grok"
