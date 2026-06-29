"""User entity: an authenticated account with a role for RBAC."""
from __future__ import annotations
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.domain.enums import UserRole
from app.domain.entities.base import IDMixin, TimestampMixin
from app.domain.entities.types import enum_column, string_column


class User(IDMixin, TimestampMixin, table=True):
    """An application user. Passwords are stored as bcrypt hashes only."""

    __tablename__ = "users"

    username: str = Field(sa_column=string_column(80, nullable=False, unique=True, index=True))
    email: str = Field(default="", sa_column=string_column(255, nullable=False, index=True))
    full_name: str = Field(default="", sa_column=string_column(150, nullable=False))
    hashed_password: str = Field(sa_column=string_column(255, nullable=False))

    role: UserRole = Field(default=UserRole.USER, sa_column=enum_column(UserRole, index=True))
    is_active: bool = Field(default=True, index=True)
    is_superuser: bool = Field(default=False)

    last_login_at: datetime | None = Field(default=None)
