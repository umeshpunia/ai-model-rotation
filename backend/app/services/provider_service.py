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
        provider = self.repo.get(provider_id)
        if not provider:
            raise NotFoundError(f"Provider with id {provider_id} not found.")
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
            slug = item.get("slug")
            if not slug:
                raise ValidationError("Missing slug in provider configuration.")
            
            existing = self.repo.get_by(slug=slug)
            if existing:
                self.repo.update(existing, item)
                imported.append(existing)
            else:
                provider = Provider(**item)
                self.repo.add(provider)
                imported.append(provider)
        return imported
