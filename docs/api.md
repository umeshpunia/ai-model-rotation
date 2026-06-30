# API Specifications

AI Gateway Pro exposes two endpoint groups:
1. **Gateway API** (`/v1/*`): OpenAI-compatible endpoints used by your apps to query LLMs.
2. **Administration API** (`/api/v1/*`): Manage credentials, settings, backups, and logs.

---

## 1. Gateway API

### Chat Completions
- **Endpoint:** `POST /v1/chat` or `POST /v1/chat/completions`
- **Request Body (JSON):**
  ```json
  {
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7
  }
  ```
- **Response Body (JSON):**
  ```json
  {
    "id": "chatcmpl-12345",
    "object": "chat.completion",
    "created": 1677652288,
    "model": "gpt-4o",
    "choices": [
      {
        "index": 0,
        "message": {
          "role": "assistant",
          "content": "Hello! How can I help you today?"
        },
        "finish_reason": "stop"
      }
    ],
    "usage": {
      "prompt_tokens": 9,
      "completion_tokens": 12,
      "total_tokens": 21
    }
  }
  ```

---

## 2. Administration API

All admin endpoints require a `Bearer <token>` JSON Web Token inside the request's Authorization header (obtained via `/api/v1/auth/login`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| **POST** | `/api/v1/auth/login` | Login credentials exchange |
| **GET** | `/api/v1/providers` | List all providers |
| **POST** | `/api/v1/providers` | Create new provider |
| **POST** | `/api/v1/providers/{id}/test` | Trigger provider connection test |
| **GET** | `/api/v1/keys` | List API keys |
| **POST** | `/api/v1/keys` | Add a new encrypted API key |
| **POST** | `/api/v1/keys/{id}/test` | Run connection test for specific key |
| **POST** | `/api/v1/keys/{id}/rotate` | Force key status rotation / cooldown |
| **GET** | `/api/v1/backups` | Retrieve database snapshots list |
| **POST** | `/api/v1/backups` | Trigger manual SQLite database backup |
| **POST** | `/api/v1/backups/{id}/restore` | Restore database snapshot |

Interactive documentation (Swagger UI) is available at `/docs` when the backend is running.
