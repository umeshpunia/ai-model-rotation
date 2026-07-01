import os
import shutil
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgentAdapter(ABC):
    @property
    @abstractmethod
    def slug(self) -> str:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def config_filename(self) -> str:
        pass

    @abstractmethod
    def get_config_path(self) -> str:
        pass

    def exists(self) -> bool:
        path = self.get_config_path()
        return path is not None and os.path.exists(path)

    def backup(self) -> str | None:
        path = self.get_config_path()
        if not path or not os.path.exists(path):
            return None
        backup_dir = os.path.join(os.path.dirname(path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        import time
        backup_path = os.path.join(backup_dir, f"{self.config_filename}.{int(time.time())}.bak")
        shutil.copy2(path, backup_path)
        return backup_path

    def restore(self) -> bool:
        path = self.get_config_path()
        if not path:
            return False
        backup_dir = os.path.join(os.path.dirname(path), "backups")
        if not os.path.exists(backup_dir):
            return False
        backups = sorted(
            [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith(self.config_filename) and f.endswith(".bak")],
            key=os.path.getmtime
        )
        if not backups:
            return False
        shutil.copy2(backups[-1], path)
        return True

    @abstractmethod
    def detect(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def wire(self, base_url: str, api_key: str, model: str) -> None:
        pass
