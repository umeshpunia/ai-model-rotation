# AI Gateway Pro

> Enterprise-grade local AI provider and API key management platform.

---

## What is AI Gateway Pro?

AI Gateway Pro is a **desktop application** that acts as a unified local gateway for all your AI provider integrations. It manages multiple AI providers, multiple API keys per provider, automatic key rotation on failure, intelligent routing and failover, health monitoring, and exposes a single REST API endpoint that all your local applications can consume.

**Instead of hardcoding one API key per provider in every app, you point everything at `http://localhost:8080` and let AI Gateway Pro handle the rest.**

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Provider Management** | Add, configure, and manage Gemini, OpenAI, Anthropic, Grok, DeepSeek, OpenRouter, Ollama, Azure OpenAI — and more via plugins. |
| **Unlimited API Keys** | Store unlimited keys per provider with AES-256-GCM encryption at rest. |
| **Automatic Key Rotation** | On 401, 403, 429, 500, 503, or timeout — automatically switch to the next available key or provider. |
| **Intelligent Routing** | Priority, Round Robin, Least Used, Fastest, Lowest Cost, Highest Success Rate, Random, AI-Optimized routing modes. |
| **Provider Failover** | Configurable priority chains with automatic fallback when all keys for a provider are exhausted. |
| **Health Monitoring** | Background workers continuously check key validity, provider availability, latency, quotas, and recovery. |
| **Secure Storage** | All API keys encrypted at rest. Master password protection. JWT authentication for the REST API. |
| **Desktop Application** | Installable .exe with system tray, auto-start, background service, Start Menu and desktop shortcuts. |
| **REST API** | Stable local REST API (`/v1/chat`, `/v1/stream`, `/v1/image`, `/v1/embedding`) for all client applications. |
| **Dashboard** | Real-time dashboard showing providers, keys, requests, latency, costs, and health status. |
| **Notifications** | Desktop, Email, Slack, Discord, Telegram, and Webhook notifications for critical events. |
| **Configuration Profiles** | Development, Production, and Testing profiles with JSON import/export and backups. |

---

## Architecture

```
+---------------------------------------------------------+
|                    Desktop UI (React + TypeScript)        |
|              Tailwind CSS, shadcn/ui, Zustand            |
+---------------------------------------------------------+
|                    REST API (FastAPI)                     |
|         /api/v1/*  (Admin)    /v1/*  (Gateway)           |
+---------------------------------------------------------+
|               Service Layer (Business Logic)              |
|     Routing, Failover, Key Rotation, Health Monitor       |
+---------------------------------------------------------+
|            Provider Plugin System (Dynamic Loading)       |
|   Gemini, OpenAI, Anthropic, Grok, DeepSeek, ...         |
+---------------------------------------------------------+
|              Repository Pattern (Data Access)             |
|          MySQL / PostgreSQL, Alembic Migrations           |
+---------------------------------------------------------+
|             Background Scheduler (APScheduler)            |
|   Health Checks, Stats, Cleanup, Backups, Recovery        |
+---------------------------------------------------------+
```

### Clean Architecture

The backend is organized into strictly separated layers:

- **Presentation** — API routers (request/response handling only)
- **Business Logic** — Services (all business rules live here)
- **Infrastructure** — Provider plugins, external HTTP clients
- **Persistence** — Repositories, database models, migrations

---

## Tech Stack

### Backend

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| Web Framework | FastAPI (async) |
| ORM | SQLModel / SQLAlchemy 2.0 |
| Database | MySQL (default) / PostgreSQL (optional) |
| Migrations | Alembic |
| Auth | JWT + bcrypt |
| Encryption | AES-256-GCM |
| HTTP Client | httpx (async) |
| Scheduler | APScheduler |
| Logging | structlog |

### Frontend

| Component | Technology |
|-----------|------------|
| Language | TypeScript |
| Framework | React |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| UI Components | shadcn/ui |
| State Management | Zustand |
| Server State | React Query |
| Routing | React Router |

### Packaging

| Component | Technology |
|-----------|------------|
| Python Packaging | PyInstaller |
| Windows Installer | Inno Setup / NSIS |
| Service | Windows Service support |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- MySQL 8.0+ (or PostgreSQL)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e ".[dev]"
copy .env.example .env        # Edit with your settings
alembic upgrade head
uvicorn app:app --host 127.0.0.1 --port 8080 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard opens at `http://localhost:5173` and the API is at `http://localhost:8080/docs`.

---

## Project Structure

```
ai-gateway-pro/
  backend/
    app/                  # FastAPI application
      core/               # Config, security, logging, database, exceptions
      domain/             # Enums, entities (SQLModel ORM)
      repositories/       # Data access layer
      services/           # Business logic + provider plugins
      routers/            # API route handlers
      schemas/            # Pydantic DTOs
      middleware/         # CORS, auth, logging middleware
    alembic/              # Database migrations
    tests/                # Unit, integration, service tests
    scripts/              # Utility scripts
    pyproject.toml        # Dependencies
  frontend/               # React + TypeScript dashboard
  docs/                   # Architecture and deployment docs
  scripts/                # Build and packaging scripts
  prompt.md               # Full project specification
  phase.md                # Development phases and status
  README.md               # This file
```

---

## API Endpoints

### Gateway (Application Integration)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/chat` | Chat completions (OpenAI-compatible) |
| POST | `/v1/stream` | Streaming chat completions |
| POST | `/v1/image` | Image generation |
| POST | `/v1/embedding` | Text embeddings |

### Administration

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Authenticate and receive JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET/POST | `/api/v1/providers` | List / create providers |
| GET/PUT/DELETE | `/api/v1/providers/{id}` | Manage a provider |
| POST | `/api/v1/providers/{id}/test` | Test provider connection |
| GET/POST | `/api/v1/keys` | List / create API keys |
| GET/PUT/DELETE | `/api/v1/keys/{id}` | Manage an API key |
| POST | `/api/v1/keys/{id}/test` | Test key validity |
| POST | `/api/v1/keys/{id}/rotate` | Manually rotate a key |
| GET | `/api/v1/models` | List available models |
| GET | `/api/v1/health` | Health status |
| GET | `/api/v1/status` | System status |
| GET | `/api/v1/statistics` | Usage statistics |
| GET | `/api/v1/logs` | Request logs |
| GET/PUT | `/api/v1/settings` | Configuration management |
| POST | `/api/v1/settings/import` | Import configuration |
| GET | `/api/v1/settings/export` | Export configuration |
| GET/PUT | `/api/v1/notifications` | Notification management |

Full interactive documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc) when the server is running.

---

## Development Phases

| # | Phase | Status |
|---|-------|--------|
| 1 | Foundation & Architecture | ✅ Complete |
| 2 | Core Infrastructure | ✅ Complete |
| 3 | Data Layer | ✅ Complete |
| 4 | Provider Plugin System | ✅ Complete |
| 5 | API Key Management | ✅ Complete |
| 6 | Intelligent Routing & Failover | ✅ Complete |
| 7 | Background Services & Health Monitoring | ✅ Complete |
| 8 | REST API | ✅ Complete |
| 9 | Notification System | ✅ Complete |
| 10 | Configuration & Profiles | ✅ Complete |
| 11 | Frontend (React + TypeScript) | 🚧 In Progress |
| 12 | Desktop Integration | ⬜ Not Started |
| 13 | Packaging & Distribution | ⬜ Not Started |
| 14 | Testing | ⬜ Not Started |
| 15 | Documentation | ⬜ Not Started |

See `phase.md` for detailed task breakdowns within each phase.

---

## Configuration

All settings are configurable via environment variables or `.env` file. No values are hardcoded. Configuration can be changed at runtime where feasible.

Key configuration groups:

- **General** — App name, environment, debug mode, log level
- **Host** — Server bind address, port, workers
- **CORS** — Allowed origins, methods, headers
- **Database** — Connection URL, pool settings
- **Security** — Secret key, JWT settings, encryption salt
- **API** — Prefixes, pagination defaults
- **Logging** — Directory, rotation, format
- **Scheduler** — Health check, stats, cleanup intervals
- **Provider** — Plugin directory, timeout, retry settings
- **Notification** — Desktop, email, Slack, Discord, Telegram, webhook
- **Backup** — Directory, retention, compression
- **Tray** — System tray, auto-start

---

## Security

- **AES-256-GCM encryption** for all API keys at rest
- **Master password** protection for the encryption key
- **JWT authentication** for REST API access
- **Role-based access control** (Admin / User / Viewer)
- **API key masking** in UI and logs — raw keys are never exposed
- **Constant-time comparison** for token validation

For details on reporting vulnerabilities, see [SECURITY.md](SECURITY.md).

---

## Testing

```bash
# Backend tests
cd backend
pytest --cov=app --cov-report=term-missing

# Frontend tests
cd frontend
npm test
```

---

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) for details on how to get started, the development workflow, and coding standards.

All contributors are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Community & Support

- 🐛 **Bug Reports**: [Open an Issue](https://github.com/umeshpunia/ai-model-rotation/issues/new?template=bug_report.md)
- 💡 **Feature Requests**: [Request a Feature](https://github.com/umeshpunia/ai-model-rotation/issues/new?template=feature_request.md)
- 📖 **Documentation**: See the `docs/` directory for architecture and deployment guides
- ⭐ **Star this repo** if you find it useful!

---

## Authors & Contributors

See [AUTHORS.md](AUTHORS.md) for the full list of contributors.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.