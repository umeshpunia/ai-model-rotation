import os
import json
from typing import Dict, Any
from app.services.agent_adapters.base import BaseAgentAdapter

class ContinueAdapter(BaseAgentAdapter):
    @property
    def slug(self) -> str:
        return "continue"

    @property
    def name(self) -> str:
        return "Continue"

    @property
    def config_filename(self) -> str:
        return "config.json"

    def get_config_path(self) -> str:
        return os.path.expanduser("~/.continue/config.json")

    def detect(self) -> Dict[str, Any]:
        path = self.get_config_path()
        if not self.exists():
            return {"exists": False, "baseUrl": "", "apiKey": "", "model": ""}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            models = data.get("models", [])
            for m in models:
                if m.get("apiBase") or m.get("apiKey"):
                    return {
                        "exists": True,
                        "baseUrl": m.get("apiBase", ""),
                        "apiKey": m.get("apiKey", ""),
                        "model": m.get("model", "")
                    }
            return {"exists": True, "baseUrl": "", "apiKey": "", "model": ""}
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
                
        # Inject our model configuration at the beginning
        new_model = {
            "title": "AI Gateway Pro",
            "provider": "openai",
            "model": model or "gpt-4o",
            "apiBase": base_url,
            "apiKey": api_key
        }
        
        models = data.get("models", [])
        # Filter out any old AI Gateway Pro model configurations
        models = [m for m in models if m.get("title") != "AI Gateway Pro"]
        models.insert(0, new_model)
        data["models"] = models
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
