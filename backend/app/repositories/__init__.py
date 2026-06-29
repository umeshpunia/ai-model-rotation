"""Repository package: data access layer for domain entities.

Every repository wraps a single entity and exposes typed CRUD plus
domain-specific queries. Repositories are constructed with an active session
and never own transactions — the caller's unit of work commits/rolls back.
"""
from __future__ import annotations

from app.repositories.base import BaseRepository
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.backup_repository import BackupRepository
from app.repositories.health_log_repository import HealthLogRepository
from app.repositories.model_repository import ModelRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.provider_repository import ProviderRepository
from app.repositories.request_log_repository import RequestLogRepository
from app.repositories.setting_repository import SettingRepository
from app.repositories.statistic_repository import StatisticRepository
from app.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "ApiKeyRepository",
    "BackupRepository",
    "HealthLogRepository",
    "ModelRepository",
    "NotificationRepository",
    "ProviderRepository",
    "RequestLogRepository",
    "SettingRepository",
    "StatisticRepository",
    "UserRepository",
]
