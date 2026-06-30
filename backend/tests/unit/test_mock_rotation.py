import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.core.database import session_scope, get_settings, dispose_engine
from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.entities.model import Model
from app.domain.enums import ApiFormat, AuthType, RoutingMode, KeyStatus, HealthStatus
from app.services.gateway_service import GatewayService
from app.schemas.gateway import ChatCompletionRequest, Message
from app.core.exceptions import UpstreamError
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

@pytest.mark.asyncio
async def test_gateway_service_key_rotation_fallback():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        key_repo = ApiKeyRepository(session)
        model_repo = ModelRepository(session)
        
        provider = Provider(
            name="OpenAI", slug="openai", plugin="openai", api_format=ApiFormat.OPENAI, auth_type=AuthType.BEARER, base_url="https://api.openai.com/v1"
        )
        provider_repo.add(provider)
        assert provider.id is not None
        
        # Add key1 (which will fail)
        key1 = ApiKey(provider_id=provider.id, name="Key 1", encrypted_key="enc1", key_hint="hint1", fingerprint="fp1", priority=1)
        # Add key2 (which will succeed)
        key2 = ApiKey(provider_id=provider.id, name="Key 2", encrypted_key="enc2", key_hint="hint2", fingerprint="fp2", priority=2)
        key_repo.add(key1)
        key_repo.add(key2)
        
        model = Model(provider_id=provider.id, name="gpt-4o", display_name="GPT-4o")
        model_repo.add(model)
        
    # Mock the plugin manager and individual plugin's chat_completion method
    mock_plugin = AsyncMock()
    
    # Configure mock responses:
    # First call raises UpstreamError(429) -> trigger rotation
    # Second call returns a valid ChatCompletionResponse mock
    from app.schemas.gateway import ChatCompletionResponse, ChatChoice, Usage
    
    mock_success_response = ChatCompletionResponse(
        id="chatcmpl-test",
        object="chat.completion",
        created=int(datetime.now(timezone.utc).timestamp()),
        model="gpt-4o",
        choices=[ChatChoice(index=0, message=Message(role="assistant", content="Hello!"), finish_reason="stop")],
        usage=Usage(prompt_tokens=5, completion_tokens=5, total_tokens=10)
    )
    
    rate_limit_err = UpstreamError("Rate Limit")
    rate_limit_err.status_code = 429
    
    mock_plugin.chat_completion.side_effect = [
        rate_limit_err,
        mock_success_response
    ]

    from unittest.mock import MagicMock
    mock_plugin_manager = MagicMock()
    mock_plugin_manager.get_plugin.return_value = mock_plugin

    with patch("app.services.api_key_service.ApiKeyService.reveal_key", return_value="dummy_raw_key"):
        with patch("app.services.api_key_service.get_plugin_manager", return_value=mock_plugin_manager):
            with patch("app.services.gateway_service.get_notification_dispatcher") as mock_dispatcher:
                with session_scope() as session:
                    gateway = GatewayService(session)
                    req = ChatCompletionRequest(
                        model="gpt-4o",
                        messages=[Message(role="user", content="Hi")]
                    )
                
                # Execute chat completion - should succeed due to fallback/rotation
                res = await gateway.execute_chat(req, RoutingMode.PRIORITY)
                assert res.choices[0].message.content == "Hello!"
                
            # Verify database states after transaction session commits
            with session_scope() as session:
                k_repo = ApiKeyRepository(session)
                db_key1 = k_repo.get(key1.id)
                db_key2 = k_repo.get(key2.id)
                
                assert db_key1 is not None
                assert db_key2 is not None
                # key1 should have been placed on cooldown
                assert db_key1.status == KeyStatus.COOLDOWN
                assert db_key1.consecutive_failures == 1
                
                # key2 should remain healthy and have successful usage recorded
                assert db_key2.status == KeyStatus.HEALTHY
                assert db_key2.success_count == 1
