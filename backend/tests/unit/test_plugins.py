import pytest
from app.services.provider_plugins import get_plugin_manager
from app.services.provider_plugins.base import BaseProviderPlugin
from app.schemas.gateway import ChatCompletionRequest, Message
from app.domain.enums import ApiFormat, AuthType
from app.services.provider_service import ProviderService
from app.repositories.provider_repository import ProviderRepository
from app.domain.entities.provider import Provider
from app.core.database import session_scope, get_settings, dispose_engine

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

def test_plugin_discovery():
    mgr = get_plugin_manager()
    mgr.discover_plugins()
    
    openai_plugin = mgr.get_plugin("openai")
    assert isinstance(openai_plugin, BaseProviderPlugin)
    assert openai_plugin.provider_slug == "openai"
    
    gemini_plugin = mgr.get_plugin("gemini")
    assert gemini_plugin.provider_slug == "gemini"

def test_gemini_message_mapping():
    mgr = get_plugin_manager()
    gemini = mgr.get_plugin("gemini")
    
    req = ChatCompletionRequest(
        model="gemini-1.5-flash",
        messages=[
            Message(role="system", content="sys-prompt"),
            Message(role="user", content="hello"),
            Message(role="assistant", content="response"),
        ]
    )
    mapped = gemini._map_messages(req.messages)
    assert len(mapped) == 3
    assert mapped[0]["role"] == "user"
    assert mapped[0]["parts"][0]["text"] == "sys-prompt"
    assert mapped[1]["role"] == "user"
    assert mapped[2]["role"] == "model"

def test_anthropic_message_mapping():
    mgr = get_plugin_manager()
    anthropic = mgr.get_plugin("anthropic")
    
    req = ChatCompletionRequest(
        model="claude-3-haiku",
        messages=[
            Message(role="system", content="sys-prompt"),
            Message(role="user", content="hello"),
        ]
    )
    mapped = anthropic._map_messages(req.messages)
    assert len(mapped) == 1
    assert mapped[0]["role"] == "user"
    assert mapped[0]["content"] == "hello"
    
    sys_msg = anthropic._get_system_message(req.messages)
    assert sys_msg == "sys-prompt"

def test_provider_service_import_export():
    with session_scope() as session:
        service = ProviderService(session)
        
        provider = Provider(
            name="OpenAI Provider",
            slug="openai",
            plugin="openai",
            api_format=ApiFormat.OPENAI,
            auth_type=AuthType.BEARER,
            base_url="https://api.openai.com/v1"
        )
        service.repo.add(provider)
        
        exported = service.export_providers()
        assert "openai" in exported
        
        imported = service.import_providers(exported)
        assert len(imported) == 1
        assert imported[0].slug == "openai"
