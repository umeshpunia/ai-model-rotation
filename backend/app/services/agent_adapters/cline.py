import os
import json
from typing import Dict, Any
from app.services.agent_adapters.base import BaseAgentAdapter

class ClineAdapter(BaseAgentAdapter):
    @property
    def slug(self) -> str:
        return "cline"

    @property
    def name(self) -> str:
        return "Cline"

    @property
    def config_filename(self) -> str:
        return "cline_persisted_state.json"

    def get_config_path(self) -> str:
        appdata = os.getenv("APPDATA")
        if appdata:
            return os.path.join(appdata, "Code", "User", "globalStorage", "saoudrizwan.claude-dev", "settings", "cline_persisted_state.json")
        return os.path.expanduser("~/.cline_persisted_state.json")

    def detect(self) -> Dict[str, Any]:
        path = self.get_config_path()
        if not self.exists():
            return {"exists": False, "baseUrl": "", "apiKey": "", "model": ""}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "exists": True,
                "baseUrl": data.get("openAiBaseUrl", ""),
                "apiKey": data.get("openAiApiKey", ""),
                "model": data.get("openAiModelId", "")
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
                
        data["apiProvider"] = "openai"
        data["openAiBaseUrl"] = base_url
        data["openAiApiKey"] = api_key
        if model:
            data["openAiModelId"] = model
            
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
