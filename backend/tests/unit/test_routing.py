import pytest
from datetime import datetime, timezone, timedelta
from app.core.database import session_scope, get_settings, dispose_engine
from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.entities.model import Model
from app.domain.enums import ApiFormat, AuthType, RoutingMode, KeyStatus
from app.services.routing_engine import RoutingEngine
from app.services.gateway_service import GatewayService
from app.schemas.gateway import ChatCompletionRequest, Message
from app.core.exceptions import ProviderUnavailableError
from app.repositories.provider_repository import ProviderRepository
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.model_repository import ModelRepository

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

def test_routing_strategies_sorting():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        key_repo = ApiKeyRepository(session)
        model_repo = ModelRepository(session)
        engine = RoutingEngine(session)
        
        provider = Provider(
            name="OpenAI", slug="openai", plugin="openai", api_format=ApiFormat.OPENAI, auth_type=AuthType.BEARER, base_url="https://api.openai.com/v1"
        )
        provider_repo.add(provider)
        
        # Explicitly declare provider.id is not None for typing
        assert provider.id is not None
        
        key1 = ApiKey(provider_id=provider.id, name="Key 1", encrypted_key="enc1", key_hint="hint1", fingerprint="fp1", usage_count=10, priority=1)
        key2 = ApiKey(provider_id=provider.id, name="Key 2", encrypted_key="enc2", key_hint="hint2", fingerprint="fp2", usage_count=2, priority=2)
        key_repo.add(key1)
        key_repo.add(key2)
        
        model = Model(provider_id=provider.id, name="gpt-4o", display_name="GPT-4o")
        model_repo.add(model)
        
        # Test PRIORITY sorting: key1 priority=1 should be first
        candidates_prio = engine.select_candidates("gpt-4o", RoutingMode.PRIORITY)
        assert len(candidates_prio) == 2
        assert candidates_prio[0][1].name == "Key 1"
        
        # Test LEAST_USED sorting: key2 usage=2 should be first
        candidates_usage = engine.select_candidates("gpt-4o", RoutingMode.LEAST_USED)
        assert candidates_usage[0][1].name == "Key 2"

def test_failover_rotation_rules():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        key_repo = ApiKeyRepository(session)
        model_repo = ModelRepository(session)
        
        provider = Provider(
            name="OpenAI", slug="openai", plugin="openai", api_format=ApiFormat.OPENAI, auth_type=AuthType.BEARER, base_url="https://api.openai.com/v1"
        )
        provider_repo.add(provider)
        
        assert provider.id is not None
        
        key = ApiKey(provider_id=provider.id, name="Key 1", encrypted_key="enc1", key_hint="hint1", fingerprint="fp1", priority=1)
        key_repo.add(key)
        
        model = Model(provider_id=provider.id, name="gpt-4o", display_name="GPT-4o")
        model_repo.add(model)
        
        service = GatewayService(session)
        
        # Test Auth error (401) rotation rule -> sets Key to INVALID and disables it
        service._handle_rotation_rules(key, 401, "Unauthorized")
        assert key.status == KeyStatus.INVALID
        assert key.is_enabled is False
        
        # Enable it again for cooldown test
        key.is_enabled = True
        key_repo.update(key, {"is_enabled": True})
        
        # Test Rate Limit (429) rotation rule -> sets Key to COOLDOWN
        service._handle_rotation_rules(key, 429, "Too Many Requests")
        assert key.status == KeyStatus.COOLDOWN
        assert key.cooldown_until > datetime.now(timezone.utc)
