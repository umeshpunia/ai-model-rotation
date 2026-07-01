from typing import Dict, List, Type
from app.services.agent_adapters.base import BaseAgentAdapter
from app.services.agent_adapters.claude_code import ClaudeCodeAdapter
from app.services.agent_adapters.aider import AiderAdapter
from app.services.agent_adapters.continue_agent import ContinueAdapter
from app.services.agent_adapters.cline import ClineAdapter
from app.services.agent_adapters.roo_code import RooCodeAdapter
from app.services.agent_adapters.goose import GooseAdapter
from app.services.agent_adapters.antigravity import AntigravityAdapter
from app.services.agent_adapters.qodo import QodoAdapter
from app.services.agent_adapters.custom import CustomAgentAdapter

class AgentAdapterManager:
    def __init__(self) -> None:
        self._adapters: Dict[str, Type[BaseAgentAdapter]] = {}
        self.register_adapter(ClaudeCodeAdapter)
        self.register_adapter(AiderAdapter)
        self.register_adapter(ContinueAdapter)
        self.register_adapter(ClineAdapter)
        self.register_adapter(RooCodeAdapter)
        self.register_adapter(GooseAdapter)
        self.register_adapter(AntigravityAdapter)
        self.register_adapter(QodoAdapter)

    def register_adapter(self, adapter_cls: Type[BaseAgentAdapter]) -> None:
        inst = adapter_cls()
        self._adapters[inst.slug] = adapter_cls

    def get_adapter(self, slug: str, custom_path: str = "") -> BaseAgentAdapter:
        if slug == "custom":
            return CustomAgentAdapter(custom_path)
        if slug not in self._adapters:
            raise ValueError(f"Unknown agent adapter slug: {slug}")
        return self._adapters[slug]()

    def list_adapters(self) -> List[BaseAgentAdapter]:
        return [cls() for cls in self._adapters.values()]
