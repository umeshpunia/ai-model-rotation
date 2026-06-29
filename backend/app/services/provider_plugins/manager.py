import os
import importlib
import inspect
from pathlib import Path
from typing import Dict, Type
from app.services.provider_plugins.base import BaseProviderPlugin
from app.core.logging import get_logger

_logger = get_logger("app")

class PluginManager:
    """Discovers, loads, and registers provider plugins dynamically."""

    def __init__(self, plugin_dir: str | None = None) -> None:
        from app.core.config import get_settings
        p_dir = plugin_dir or get_settings().provider.plugin_directory
        self.plugin_dir = Path(p_dir).resolve()
        self._plugins: Dict[str, BaseProviderPlugin] = {}

    def discover_plugins(self) -> None:
        """Scan directory and import all modules inheriting from BaseProviderPlugin."""
        if not self.plugin_dir.exists():
            _logger.warning("plugins.directory.missing", path=str(self.plugin_dir))
            return
        
        for file in self.plugin_dir.glob("*.py"):
            if file.name in ("__init__.py", "base.py", "manager.py"):
                continue
            module_name = f"app.services.provider_plugins.{file.stem}"
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, BaseProviderPlugin)
                        and attr is not BaseProviderPlugin
                    ):
                        plugin_inst = attr()
                        self._plugins[plugin_inst.provider_slug] = plugin_inst
                        _logger.info("plugin.registered", slug=plugin_inst.provider_slug)
            except Exception as e:
                _logger.error("plugin.import.failed", module=module_name, error=str(e))

    def get_plugin(self, slug: str) -> BaseProviderPlugin:
        if not self._plugins:
            self.discover_plugins()
        if slug not in self._plugins:
            raise KeyError(f"No provider plugin registered for slug: {slug}")
        return self._plugins[slug]

_manager = PluginManager()

def get_plugin_manager() -> PluginManager:
    return _manager
