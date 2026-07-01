import os
import yaml
from typing import Dict, Any
from app.services.agent_adapters.base import BaseAgentAdapter

class AiderAdapter(BaseAgentAdapter):
    @property
    def slug(self) -> str:
        return "aider"

    @property
    def name(self) -> str:
        return "Aider"

    @property
    def config_filename(self) -> str:
        return ".aider.conf.yml"

    def get_config_path(self) -> str:
        return os.path.expanduser("~/.aider.conf.yml")

    def detect(self) -> Dict[str, Any]:
        path = self.get_config_path()
        if not self.exists():
            return {"exists": False, "baseUrl": "", "apiKey": "", "model": ""}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return {
                "exists": True,
                "baseUrl": data.get("openai-api-base", ""),
                "apiKey": data.get("openai-api-key", ""),
                "model": data.get("model", "")
            }
        except Exception:
            return {"exists": True, "baseUrl": "", "apiKey": "", "model": ""}

    def wire(self, base_url: str, api_key: str, model: str) -> None:
        path = self.get_config_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            except Exception:
                pass
                
        data["openai-api-base"] = base_url
        data["openai-api-key"] = api_key
        if model:
            data["model"] = model
            
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
