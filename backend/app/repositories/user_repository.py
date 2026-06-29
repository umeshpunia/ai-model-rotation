"""Repository for :class:`User` entities."""
from __future__ import annotations

from app.domain.entities.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data access for user accounts."""

    model = User

    def get_by_username(self, username: str) -> User | None:
        """Return a user by unique username."""
        return self.get_by(username=username)

    def get_by_email(self, email: str) -> User | None:
        """Return a user by email address."""
        return self.get_by(email=email)

    def list_active(self) -> list[User]:
        """Return all active users ordered by username."""
        return self.list(filters={"is_active": True}, order_by=User.username.asc())

    def username_exists(self, username: str, *, exclude_id: int | None = None) -> bool:
        """Whether a username is taken (optionally excluding one user id)."""
        existing = self.get_by_username(username)
        if existing is None:
            return False
        return exclude_id is None or existing.id != exclude_id

    def count_admins(self) -> int:
        """Count superuser accounts (guards against removing the last admin)."""
        return self.count(filters={"is_superuser": True})
