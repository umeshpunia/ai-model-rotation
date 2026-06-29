from abc import ABC, abstractmethod
from typing import Any

class BaseNotificationChannel(ABC):
    """Abstract base class for all notification channels."""

    @abstractmethod
    async def send(self, title: str, message: str, meta: dict[str, Any] | None = None) -> bool:
        """Asynchronously send notification. Return True if successful."""
        pass
