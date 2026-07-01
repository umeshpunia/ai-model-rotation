import os
import json
from typing import Dict, Any
from app.services.agent_adapters.base import BaseAgentAdapter

class AntigravityAdapter(BaseAgentAdapter):
    @property
    def slug(self) -> str:
        return "antigravity"

    @property
    def name(self) -> str:
        return "Antigravity"

    @property
    def config_filename(self) -> str:
        return "settings.json"

    def get_config_path(self) -> str:
        return os.path.expanduser("~/.antigravity/settings.json")

    def detect(self) -> Dict[str, Any]:
        path = self.get_config_path()
        if not self.exists():
            return {"exists": False, "baseUrl": "", "apiKey": "", "model": ""}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "exists": True,
                "baseUrl": data.get("baseUrl", ""),
                "apiKey": data.get("apiKey", ""),
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
                    data = json.load(f)
            except Exception:
                pass
                
        data["baseUrl"] = base_url
        data["apiKey"] = api_key
        if model:
            data["model"] = model
            
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
