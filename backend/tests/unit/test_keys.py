import pytest
from app.core.database import session_scope, get_settings, dispose_engine
from app.services.api_key_service import ApiKeyService
from app.repositories.provider_repository import ProviderRepository
from app.domain.entities.provider import Provider
from app.domain.enums import ApiFormat, AuthType, KeyStatus
from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate
from app.core.exceptions import ValidationError

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

def test_api_key_lifecycle_and_encryption():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        service = ApiKeyService(session)
        
        provider = Provider(
            name="OpenAI Provider",
            slug="openai",
            plugin="openai",
            api_format=ApiFormat.OPENAI,
            auth_type=AuthType.BEARER,
            base_url="https://api.openai.com/v1"
        )
        provider_repo.add(provider)
        
        # Test creation & encryption
        assert provider.id is not None
        create_payload = ApiKeyCreate(
            provider_id=provider.id,
            name="Main Key",
            key="sk-proj-super-secret-key-material-here"
        )
        key_rec = service.create_key(create_payload)
        assert key_rec.id is not None
        assert key_rec.key_hint.startswith("sk-p")
        assert "super-secret" not in key_rec.encrypted_key  # encrypted opaque JSON blob
        
        # Test decryption/reveal
        decrypted = service.reveal_key(key_rec.id)
        assert decrypted == "sk-proj-super-secret-key-material-here"
        
        # Test duplicate verification (should raise ValidationError)
        with pytest.raises(ValidationError):
            service.create_key(create_payload)

        # Test update without changing credential
        update_payload = ApiKeyUpdate(name="Renamed Key", priority=50)
        updated = service.update_key(key_rec.id, update_payload)
        assert updated.name == "Renamed Key"
        assert updated.priority == 50
        assert service.reveal_key(key_rec.id) == "sk-proj-super-secret-key-material-here"

        # Test delete
        service.delete_key(key_rec.id)
        assert service.repo.get(key_rec.id) is None
