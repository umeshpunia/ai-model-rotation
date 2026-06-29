"""User and authentication request/response DTOs."""
from datetime import datetime

from pydantic import EmailStr, Field

from app.domain.enums import UserRole
from app.schemas.common import ORMSchema, SchemaBase


class UserCreate(SchemaBase):
    """Payload for creating a user account."""

    username: str = Field(min_length=3, max_length=80)
    email: EmailStr | None = None
    full_name: str = Field(default="", max_length=150)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(SchemaBase):
    """Partial update payload for a user account."""

    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=150)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: UserRole | None = None
    is_active: bool | None = None


class UserRead(ORMSchema):
    """A user account as returned by the API (no password material)."""

    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    is_superuser: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class LoginRequest(SchemaBase):
    """Username/password login payload."""

    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(ORMSchema):
    """Issued JWT access/refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds.")


class RefreshRequest(SchemaBase):
    """Payload for refreshing an access token."""

    refresh_token: str = Field(min_length=1)
