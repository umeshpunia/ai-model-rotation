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
