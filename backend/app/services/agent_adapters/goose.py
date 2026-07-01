import os
import yaml
from typing import Dict, Any
from app.services.agent_adapters.base import BaseAgentAdapter

class GooseAdapter(BaseAgentAdapter):
    @property
    def slug(self) -> str:
        return "goose"

    @property
    def name(self) -> str:
        return "Goose"

    @property
    def config_filename(self) -> str:
        return "config.yaml"

    def get_config_path(self) -> str:
        return os.path.expanduser("~/.goose/config.yaml")

    def detect(self) -> Dict[str, Any]:
        path = self.get_config_path()
        if not self.exists():
            return {"exists": False, "baseUrl": "", "apiKey": "", "model": ""}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            openai = data.get("openai", {})
            return {
                "exists": True,
                "baseUrl": openai.get("api_base", ""),
                "apiKey": openai.get("api_key", ""),
                "model": openai.get("model", "")
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
                
        if "openai" not in data:
            data["openai"] = {}
            
        data["openai"]["api_base"] = base_url
        data["openai"]["api_key"] = api_key
        if model:
            data["openai"]["model"] = model
            
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
