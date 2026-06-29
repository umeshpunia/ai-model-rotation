"""Domain entities (SQLModel ORM classes) and shared mixins.

Importing this package registers every table on ``SQLModel.metadata`` so that
Alembic autogeneration and ``create_all`` see the full schema. Add new entities
to the imports below to include them in migrations.
"""
from __future__ import annotations

from app.domain.entities.base import IDMixin, TimestampMixin, utcnow
from app.domain.entities.api_key import ApiKey
from app.domain.entities.backup import Backup
from app.domain.entities.health_log import HealthLog
from app.domain.entities.model import Model
from app.domain.entities.notification import Notification
from app.domain.entities.provider import Provider
from app.domain.entities.request_log import RequestLog
from app.domain.entities.setting import Setting
from app.domain.entities.statistic import Statistic
from app.domain.entities.user import User

__all__ = [
    "IDMixin",
    "TimestampMixin",
    "utcnow",
    "ApiKey",
    "Backup",
    "HealthLog",
    "Model",
    "Notification",
    "Provider",
    "RequestLog",
    "Setting",
    "Statistic",
    "User",
]
