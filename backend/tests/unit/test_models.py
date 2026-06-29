import pytest
from sqlalchemy import text
from sqlmodel import select
from app.core.database import session_scope, get_settings, dispose_engine
from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.entities.model import Model
from app.domain.entities.user import User
from app.domain.enums import ApiFormat, AuthType, ProviderStatus, KeyStatus, UserRole

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

def test_provider_creation_and_defaults():
    with session_scope() as session:
        provider = Provider(
            name="OpenAI Provider",
            slug="openai",
            plugin="openai_plugin",
            api_format=ApiFormat.OPENAI,
            auth_type=AuthType.BEARER,
            base_url="https://api.openai.com/v1"
        )
        session.add(provider)
        session.flush()
        
        assert provider.id is not None
        assert provider.status == ProviderStatus.ENABLED
        assert provider.is_enabled is True
        assert provider.priority == 100

def test_provider_key_and_model_relationships():
    with session_scope() as session:
        provider = Provider(
            name="Gemini Provider",
            slug="gemini",
            plugin="gemini_plugin",
            api_format=ApiFormat.GEMINI,
            auth_type=AuthType.HEADER,
            base_url="https://generativelanguage.googleapis.com"
        )
        session.add(provider)
        session.flush()
        
        key = ApiKey(
            provider_id=provider.id,
            name="Gemini Primary Key",
            encrypted_key="encrypted-key-blob-nonce",
            priority=10
        )
        model = Model(
            provider_id=provider.id,
            name="gemini-1.5-flash",
            display_name="Gemini 1.5 Flash",
            context_window=1000000,
            input_cost_per_1k=0.000075,
            output_cost_per_1k=0.0003
        )
        session.add_all([key, model])
        session.flush()
        session.refresh(provider)
        
        assert len(provider.api_keys) == 1
        assert provider.api_keys[0].name == "Gemini Primary Key"
        assert len(provider.models) == 1
        assert provider.models[0].name == "gemini-1.5-flash"

def test_cascade_deletion():
    with session_scope() as session:
        provider = Provider(
            name="Anthropic Provider",
            slug="anthropic",
            plugin="anthropic_plugin",
            api_format=ApiFormat.ANTHROPIC,
            auth_type=AuthType.BEARER,
            base_url="https://api.anthropic.com"
        )
        session.add(provider)
        session.flush()
        
        key = ApiKey(
            provider_id=provider.id,
            name="Claude Primary Key",
            encrypted_key="encrypted-key",
            priority=10
        )
        session.add(key)
        session.flush()
        
        provider_id = provider.id
        key_id = key.id
        
        # Verify both exist
        assert session.get(Provider, provider_id) is not None
        assert session.get(ApiKey, key_id) is not None
        
        # Delete provider and check cascade delete on ApiKey
        session.delete(provider)
        session.flush()
        
        assert session.get(Provider, provider_id) is None
        assert session.get(ApiKey, key_id) is None

def test_user_creation():
    with session_scope() as session:
        user = User(
            username="admin",
            email="[email protected]",
            hashed_password="hashed_bcrypt_password_here",
            role=UserRole.ADMIN
        )
        session.add(user)
        session.flush()
        
        assert user.id is not None
        assert user.is_active is True
