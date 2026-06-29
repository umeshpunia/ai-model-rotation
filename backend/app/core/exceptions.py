"""Custom application exceptions with HTTP-friendly mappings."""
from __future__ import annotations
from typing import Any


class AppError(Exception):
    """Base class for all application exceptions."""
    status_code: int = 500
    code: str = "app_error"

    def __init__(self, message: str = "", *, details: Any | None = None) -> None:
        super().__init__(message)
        self.message = message or self.__class__.__name__
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class AlreadyExistsError(AppError):
    status_code = 409
    code = "already_exists"


class ValidationError(AppError):
    status_code = 422
    code = "validation_error"


class AuthenticationError(AppError):
    status_code = 401
    code = "authentication_error"


class AuthorizationError(AppError):
    status_code = 403
    code = "authorization_error"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class UpstreamError(AppError):
    """AI provider returned an error."""
    status_code = 502
    code = "upstream_error"


class KeyRotationExhaustedError(AppError):
    """All keys for the provider(s) have been exhausted mid-request."""
    status_code = 503
    code = "key_rotation_exhausted"


class ProviderUnavailableError(AppError):
    """Provider is disabled / offline / has no usable keys."""
    status_code = 503
    code = "provider_unavailable"


class ConfigurationError(AppError):
    """Misconfiguration that cannot be recovered from at runtime."""
    status_code = 500
    code = "configuration_error"


class EncryptionError(AppError):
    """Encryption / decryption failure."""
    status_code = 500
    code = "encryption_error"


class DatabaseError(AppError):
    """Database-related failure (distinct from sqlalchemy exceptions)."""
    status_code = 500
    code = "database_error"


class PluginError(AppError):
    """Provider plugin loading or invocation error."""
    status_code = 500
    code = "plugin_error"