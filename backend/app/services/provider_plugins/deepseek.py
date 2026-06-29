from app.services.provider_plugins.openai import OpenAIProviderPlugin

class DeepSeekProviderPlugin(OpenAIProviderPlugin):
    @property
    def provider_slug(self) -> str:
        return "deepseek"
