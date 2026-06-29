import os
import pytest
from pydantic import ValidationError
from app.core.config import get_settings, reload_settings, SecuritySettings

def test_settings_load():
    settings = get_settings()
    assert settings.general.app_name == "AI Gateway Pro"
    assert settings.database.pool_size == 10

def test_security_validation():
    # Verify key length constraint (>= 32)
    with pytest.raises(ValidationError):
        SecuritySettings(secret_key="short-key")
        
    # Verify salt length constraint (>= 8)
    with pytest.raises(ValidationError):
        SecuritySettings(master_password_salt="short")

def test_settings_hot_reload():
    os.environ["LOG_LEVEL"] = "DEBUG"
    settings = reload_settings()
    try:
        assert settings.general.log_level == "DEBUG"
    finally:
        os.environ["LOG_LEVEL"] = "INFO"
        reload_settings()
