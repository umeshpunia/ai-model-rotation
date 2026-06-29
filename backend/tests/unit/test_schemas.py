import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate
from app.schemas.provider import ProviderCreate
from app.domain.enums import ApiFormat, AuthType

def test_user_schema_validation():
    # Valid input using custom project domain to avoid reserved name and scrubber issues
    user = UserCreate(
        username="john_doe",
        email="john.doe@aigateway.pro",
        password="securepassword123"
    )
    assert user.username == "john_doe"
    
    # Invalid email
    with pytest.raises(ValidationError):
        UserCreate(
            username="john_doe",
            email="not-an-email",
            password="securepassword123"
        )

def test_provider_schema_validation():
    # Valid input
    provider = ProviderCreate(
        name="Grok Provider",
        slug="grok",
        plugin="grok_plugin",
        api_format=ApiFormat.OPENAI,
        auth_type=AuthType.BEARER,
        base_url="https://api.x.ai/v1"
    )
    assert provider.slug == "grok"
    
    # Missing required field base_url
    with pytest.raises(ValidationError):
        ProviderCreate(
            name="Grok Provider",
            slug="grok",
            plugin="grok_plugin",
            api_format=ApiFormat.OPENAI,
            auth_type=AuthType.BEARER
        )
