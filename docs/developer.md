# Developer & Contribution Guide

This guide details the internal patterns, architectures, and guidelines for extending **AI Gateway Pro**.

---

## 1. Architectural Philosophy

We strictly adhere to **Clean Architecture** principles. Concerns are divided into separated layers to ensure decoupling and maintainability:

```
[ Presentation Layer ]  -->  FastAPI Router Handlers
        |
        v
[ Business Logic ]      -->  Services (Gateway, Auth, Backup, Notifications)
        |
        v
[ Infrastructure ]     -->  Provider Plugins, AES Encryption, Schedulers
        |
        v
[ Persistence Layer ]   -->  Repositories (SQLModel entities, sessions)
```

- **Domain/Entities** (`backend/app/domain/`): Contains core structures (tables) and enums.
- **Repositories** (`backend/app/repositories/`): Data-access helpers. API routers/services should never query SQLModel directly; they must interact via repository wrappers.
- **Services** (`backend/app/services/`): Implements business rule flows (e.g. routing strategies, failovers, backups).

---

## 2. Extending the Provider Plugin System

To integrate a new LLM provider (e.g. Cohere or an internal custom model):

1. **Create the Plugin Class**: Create a new file under `backend/app/services/provider_plugins/` inheriting from `BaseProviderPlugin`:
   ```python
   from app.services.provider_plugins.base import BaseProviderPlugin
   from app.schemas.gateway import ChatCompletionRequest, ChatCompletionResponse

   class CustomProviderPlugin(BaseProviderPlugin):
       async def chat_completion(self, api_key: str, base_url: str, request: ChatCompletionRequest, config: dict) -> ChatCompletionResponse:
           # Execute HTTP calls to the model engine
           pass
   ```
2. **Register the Plugin**: Register the plugin in `backend/app/services/provider_plugins/manager.py`. The routing service discovers plugins dynamically.

---

## 3. Testing Conventions

All new logic must be tested. We use **pytest** for testing:

- **Unit tests** reside in `backend/tests/unit/`.
- **Integration tests** reside in `backend/tests/integration/`.
- **Smoke tests** reside in `backend/tests/smoke/`.

### Run tests locally:
```bash
cd backend
.venv\Scripts\pytest tests/ -v
```
Ensure all tests compile and pass cleanly before submitting pull requests.

---

## 4. Routing AI Coding Assistants through AI Gateway Pro

AI Gateway Pro acts as a local proxy, enabling you to route popular AI-driven coding engines and IDE extensions through a single URL. This guarantees automated API key rotation, cost tracking, and failover support.

### A. Claude Code (Anthropic CLI)
To route the official **Claude Code** CLI through the gateway:
1. Go to the admin dashboard's **Settings & Backups** page.
2. In the **Claude CLI Configuration** card, configure:
   - **Claude Base URL**: `http://localhost:8080/v1` (to route through the gateway) or a custom proxy like `https://capi.aerolink.lat/`.
   - **Claude API Key**: Enter your key or a valid gateway access credential.
3. Click **Update Claude Config**. This automatically updates and backs up your local `~/.claude/settings.json` configuration file.
4. Alternatively, you can click **Restore Claude Backup** to instantly restore your previous configurations.

### B. VS Code Coding Extensions (Continue, Roo Code, Cline)
To route extensions like **Continue**, **Roo Code**, or **Cline**:
- **Roo Code / Cline**:
  1. Open the extension configuration screen in VS Code.
  2. Select **OpenAI Compatible** as the provider.
  3. Set the **API URL** to: `http://localhost:8080/v1`
  4. Specify your model (e.g., `gpt-4o` or `claude-3-5-sonnet-20241022`).
- **Continue**:
  Add the following model entry to your global `~/.continue/config.json`:
  ```json
  {
    "models": [
      {
        "title": "AI Gateway Sonnet",
        "provider": "openai",
        "model": "claude-3-5-sonnet-20241022",
        "apiBase": "http://localhost:8080/v1"
      }
    ]
  }
  ```

### C. Antigravity IDE (Advanced Coding Assistant)
To leverage the gateway's rotatable key layout inside the **Antigravity IDE**:
1. Configure your local agent's backend config/environment endpoints to query:
   ```
   http://localhost:8080/v1/chat/completions
   ```
2. The gateway will intercept completion requests, transparently manage key rotation, log token costs, and return the response.

