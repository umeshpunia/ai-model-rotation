import os
import json
from typing import Dict, Any
from app.services.agent_adapters.base import BaseAgentAdapter

class CustomAgentAdapter(BaseAgentAdapter):
    def __init__(self, custom_path: str = "") -> None:
        self.custom_path = custom_path

    @property
    def slug(self) -> str:
        return "custom"

    @property
    def name(self) -> str:
        return "Custom Agent"

    @property
    def config_filename(self) -> str:
        return os.path.basename(self.custom_path) if self.custom_path else "config.json"

    def get_config_path(self) -> str:
        return self.custom_path

    def detect(self) -> Dict[str, Any]:
        path = self.get_config_path()
        if not path or not self.exists():
            return {"exists": False, "baseUrl": "", "apiKey": "", "model": ""}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "exists": True,
                "baseUrl": data.get("api_base", data.get("baseUrl", "")),
                "apiKey": data.get("api_key", data.get("apiKey", "")),
                "model": data.get("model", "")
            }
        except Exception:
            return {"exists": True, "baseUrl": "", "apiKey": "", "model": ""}

    def wire(self, base_url: str, api_key: str, model: str) -> None:
        path = self.get_config_path()
        if not path:
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        data = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
                
        data["api_base"] = base_url
        data["api_key"] = api_key
        if model:
            data["model"] = model
            
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
