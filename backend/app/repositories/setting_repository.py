"""Repository for :class:`Setting` entities."""
from __future__ import annotations
from typing import Any

from app.domain.entities.setting import Setting
from app.repositories.base import BaseRepository


class SettingRepository(BaseRepository[Setting]):
    """Data access for persisted application settings."""

    model = Setting

    def get_by_key(self, key: str, *, profile: str = "default") -> Setting | None:
        """Return a setting by key within a profile."""
        return self.get_by(key=key, profile=profile)

    def list_by_group(self, group: str, *, profile: str = "default") -> list[Setting]:
        """Return all settings in a group for a profile."""
        return self.list(
            filters={"group": group, "profile": profile},
            order_by=Setting.key.asc(),
        )

    def list_for_profile(self, profile: str = "default") -> list[Setting]:
        """Return every setting for a profile."""
        return self.list(filters={"profile": profile}, order_by=Setting.key.asc())

    def upsert(
        self,
        key: str,
        value: Any,
        *,
        profile: str = "default",
        value_type: str = "string",
        group: str = "general",
        is_secret: bool = False,
        description: str = "",
    ) -> Setting:
        """Insert or update a setting by (key, profile)."""
        existing = self.get_by_key(key, profile=profile)
        if existing is not None:
            return self.update(
                existing,
                {"value": value, "value_type": value_type, "group": group, "is_secret": is_secret},
            )
        return self.create(
            key=key,
            value=value,
            value_type=value_type,
            group=group,
            is_secret=is_secret,
            description=description,
            profile=profile,
        )
