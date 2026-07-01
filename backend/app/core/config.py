"""Application settings sourced from environment variables or `.env` file."""
from __future__ import annotations
from functools import lru_cache
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import APP_NAME, APP_VERSION


class _Base(BaseSettings):
    """Base settings: env loading + case insensitive matching."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def _csv_to_list(v: Any) -> Any:
    """Parse a comma- or JSON-list string into a Python list."""
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return []
        if v.startswith("["):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in v.split(",") if item.strip()]
    return v


class GeneralSettings(_Base):
    """General runtime settings."""
    app_name: str = APP_NAME
    app_version: str = APP_VERSION
    app_env: Literal["development", "testing", "production"] = "development"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


class HostSettings(_Base):
    """Server bind settings."""
    host: str = "127.0.0.1"
    port: int = 8080
    workers: int = 1
    reload: bool = False


class CorsSettings(_Base):
    """CORS configuration."""
    cors_origins: list[str] = Field(default_factory=lambda: [
        "http://localhost:5173",
        "http://localhost:8080",
    ])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse(cls, v: Any) -> Any:
        return _csv_to_list(v)

    @field_validator("cors_allow_methods", mode="before")
    @classmethod
    def _parse_methods(cls, v: Any) -> Any:
        return _csv_to_list(v)

    @field_validator("cors_allow_headers", mode="before")
    @classmethod
    def _parse_headers(cls, v: Any) -> Any:
        return _csv_to_list(v)


class DatabaseSettings(_Base):
    """MySQL connectivity settings."""
    database_url: str = (
        "mysql+pymysql://root:@localhost:3306/aigateway?charset=utf8mb4"
    )
    database_test_url: str = (
        "mysql+pymysql://root:@localhost:3306/aigateway_test?charset=utf8mb4"
    )
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    echo: bool = False


class SecuritySettings(_Base):
    """Cryptographic and authentication settings."""
    secret_key: str = "change-me-please-32-chars-min-default-secret-key"
    master_password_salt: str = "change-me-salt-12-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440
    jwt_refresh_token_expire_minutes: int = 43200

    @field_validator("secret_key")
    @classmethod
    def _min_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters.")
        return v

    @field_validator("master_password_salt")
    @classmethod
    def _min_salt(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("MASTER_PASSWORD_SALT must be at least 8 characters.")
        return v


class ApiSettings(_Base):
    """API surface settings."""
    api_prefix: str = "/api"
    api_v1_prefix: str = "/api/v1"
    gateway_prefix: str = "/v1"
    page_size_default: int = 20
    page_size_max: int = 200


class LoggingSettings(_Base):
    """Logging destination / rotation settings."""
    log_dir: str = "./logs"
    log_rotation: str = "20 MB"
    log_retention: int = 14
    log_format: Literal["json", "console"] = "json"


class SchedulerSettings(_Base):
    """Background scheduler timing in seconds."""
    scheduler_enabled: bool = True
    health_check_interval_seconds: int = 300
    statistics_aggregation_interval_seconds: int = 600
    log_cleanup_interval_seconds: int = 3600
    backup_interval_seconds: int = 86400
    notification_cleanup_interval_seconds: int = 7200


class ProviderSettings(_Base):
    """Provider plugin-related settings."""
    plugin_directory: str = "./app/services/provider_plugins"
    provider_timeout_seconds: int = 120
    provider_max_retries: int = 3
    provider_retry_backoff_seconds: float = 2.0
    provider_cooldown_seconds: int = 60


class NotificationSettings(_Base):
    """Notification target configuration."""
    desktop_enabled: bool = True
    email_enabled: bool = False
    slack_enabled: bool = False
    discord_enabled: bool = False
    telegram_enabled: bool = False
    webhook_enabled: bool = False
    email_smtp: str = ""
    email_from: str = ""
    email_to: str = ""
    slack_webhook: str = ""
    discord_webhook: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    webhook_url: str = ""


class BackupSettings(_Base):
    """Local backup settings."""
    backup_directory: str = "./backups"
    backup_keep_count: int = 7
    backup_compression: bool = True


class TraySettings(_Base):
    """System tray / autostart."""
    tray_enabled: bool = True
    auto_start_with_windows: bool = False


class Settings:
    """Composite settings aggregator (no monolithic BaseSettings god class)."""

    def __init__(self) -> None:
        self.general = GeneralSettings()
        self.host = HostSettings()
        self.cors = CorsSettings()
        self.database = DatabaseSettings()
        self.security = SecuritySettings()
        self.api = ApiSettings()
        self.logging = LoggingSettings()
        self.scheduler = SchedulerSettings()
        self.provider = ProviderSettings()
        self.notification = NotificationSettings()
        self.backup = BackupSettings()
        self.tray = TraySettings()

    @property
    def is_production(self) -> bool:
        return self.general.app_env == "production"

    @property
    def is_testing(self) -> bool:
        return self.general.app_env == "testing"

    @property
    def is_development(self) -> bool:
        return self.general.app_env == "development"

    @property
    def database_url(self) -> str:
        return self.database.database_test_url if self.is_testing else self.database.database_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a singleton Settings instance."""
    return Settings()


def reload_settings() -> Settings:
    """Clear cached settings and re-read from environment (used for hot-reload)."""
    get_settings.cache_clear()
    return get_settings()