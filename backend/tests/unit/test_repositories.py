import pytest
from app.core.database import session_scope, get_settings, dispose_engine
from app.repositories.provider_repository import ProviderRepository
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.user_repository import UserRepository
from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.entities.user import User
from app.domain.enums import ApiFormat, AuthType, KeyStatus

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

def test_base_repository_crud():
    with session_scope() as session:
        repo = ProviderRepository(session)
        
        # Test Create / Add
        provider = Provider(
            name="OpenAI Provider",
            slug="openai",
            plugin="openai_plugin",
            api_format=ApiFormat.OPENAI,
            auth_type=AuthType.BEARER,
            base_url="https://api.openai.com/v1"
        )
        repo.add(provider)
        
        provider_id = provider.id
        assert provider_id is not None
        
        # Test Read / Get
        fetched = repo.get(provider_id)
        assert fetched is not None
        assert fetched.slug == "openai"
        
        # Test Update
        repo.update(fetched, {"name": "OpenAI Enterprise"})
        refetched = repo.get(provider_id)
        assert refetched.name == "OpenAI Enterprise"
        
        # Test List / Count
        providers = repo.list()
        assert len(providers) == 1
        assert repo.count() == 1
        
        # Test Paginate
        items, total = repo.paginate(offset=0, limit=10)
        assert len(items) == 1
        assert total == 1
        
        # Test Delete
        repo.delete(refetched)
        assert repo.get(provider_id) is None

def test_specific_repository_helpers():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        key_repo = ApiKeyRepository(session)
        user_repo = UserRepository(session)
        
        provider = Provider(
            name="Gemini Provider",
            slug="gemini",
            plugin="gemini_plugin",
            api_format=ApiFormat.GEMINI,
            auth_type=AuthType.BEARER,
            base_url="https://generativelanguage.googleapis.com"
        )
        provider_repo.add(provider)
        
        key = ApiKey(
            provider_id=provider.id,
            name="Key Active",
            encrypted_key="cipher-active",
            status=KeyStatus.HEALTHY,
            is_enabled=True,
            priority=1
        )
        key_disabled = ApiKey(
            provider_id=provider.id,
            name="Key Disabled",
            encrypted_key="cipher-disabled",
            status=KeyStatus.DISABLED,
            is_enabled=False,
            priority=2
        )
        key_repo.add(key)
        key_repo.add(key_disabled)
        
        # Test ApiKeyRepository helper to fetch active/usable keys for provider
        active_keys = key_repo.list_usable(provider.id)
        assert len(active_keys) == 1
        assert active_keys[0].name == "Key Active"
        
        # Test UserRepository helper to fetch by username
        user = User(
            username="umesh",
            email="[email protected]",
            hashed_password="hashed_password",
        )
        user_repo.add(user)
        
        fetched_user = user_repo.get_by_username("umesh")
        assert fetched_user is not None
        assert fetched_user.email == "[email protected]"
        
        assert user_repo.get_by_username("nonexistent") is None
