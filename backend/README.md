# AI Gateway Pro — Backend

> Python 3.11+ / FastAPI / SQLModel / MySQL (default) · PostgreSQL (optional)

---

## Overview

The backend powers the **AI Gateway Pro** desktop application. It exposes a local REST API for managing AI providers, API keys, intelligent routing, health monitoring, and failover. The architecture follows **Clean Architecture** principles: Presentation → Business Logic → Infrastructure → Persistence.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Web framework | FastAPI (async) |
| ORM | SQLModel / SQLAlchemy 2.0 |
| Database | MySQL (default) · PostgreSQL (optional) |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Encryption | AES-256-GCM (cryptography) |
| HTTP client | httpx (async) |
| Scheduler | APScheduler |
| Logging | structlog + rotating file handlers |
| Validation | Pydantic v2 + pydantic-settings |

---

## Project Structure

```
backend/
├── app/
│   ├── core/               # Cross-cutting concerns
│   │   ├── config.py       # Multi-group settings (env / .env)
│   │   ├── constants.py    # Application constants
│   │   ├── database.py     # Engine, session factory, get_db()
│   │   ├── exceptions.py   # Exception hierarchy with HTTP mapping
│   │   ├── logging.py      # Structured logging (5 channels)
│   │   └── security.py     # AES-GCM encryption, JWT, bcrypt
│   ├── domain/
│   │   ├── enums.py        # All domain enumerations
│   │   └── entities/       # SQLModel ORM classes
│   │       ├── base.py     # IDMixin, TimestampMixin
│   │       ├── provider.py
│   │       ├── api_key.py
│   │       ├── model.py
│   │       ├── user.py
│   │       ├── request_log.py
│   │       ├── health_log.py
│   │       ├── setting.py
│   │       ├── statistic.py
│   │       ├── notification.py
│   │       └── backup.py
│   ├── repositories/       # Repository pattern (CRUD + queries)
│   │   ├── base.py         # Generic BaseRepository[TEntity]
│   │   ├── provider_repository.py
│   │   ├── api_key_repository.py
│   │   ├── user_repository.py
│   │   └── ...
│   ├── services/           # Business logic layer
│   │   └── provider_plugins/  # Plugin-based provider implementations
│   ├── routers/            # API route handlers
│   ├── schemas/            # Pydantic request/response DTOs
│   └── middleware/         # CORS, auth, logging middleware
├── alembic/                # Database migrations
│   ├── env.py
│   └── versions/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── services/
├── docs/                   # Backend-specific documentation
├── scripts/                # Utility scripts
├── .env.example            # Environment template
├── alembic.ini             # Alembic configuration
└── pyproject.toml          # Dependencies & tool config
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- MySQL 8.0+ (or PostgreSQL)
- pip or poetry

### Installation

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -e ".[dev]"
```

### Configuration

```bash
copy .env.example .env        # Windows
# cp .env.example .env        # macOS / Linux
```

Edit `.env` and set at minimum:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | MySQL / PostgreSQL connection string |
| `SECRET_KEY` | ≥ 32 chars — used for JWT signing |
| `MASTER_PASSWORD_SALT` | ≥ 8 chars — used for key encryption |

### Database Setup

```bash
# Run migrations
alembic upgrade head

# Or create all tables directly in code
python -c "from app.core.database import create_tables; create_tables()"
```

### Run the Server

```bash
uvicorn app:app --host 127.0.0.1 --port 8080 --reload
```

The API is then available at `http://127.0.0.1:8080/docs` (Swagger UI).

---

## Architecture

### Clean Architecture Layers

```
┌──────────────────────────────────────────┐
│           Presentation (routers/)        │
├──────────────────────────────────────────┤
│        Business Logic (services/)        │
├──────────────────────────────────────────┤
│       Infrastructure (providers, HTTP)   │
├──────────────────────────────────────────┤
│     Persistence (repositories, models)   │
└──────────────────────────────────────────┘
```

- **Routers** handle HTTP request/response only.
- **Services** contain all business rules.
- **Repositories** abstract database access (no SQL in services).
- **Entities** define the database schema via SQLModel.

### Dependency Injection

FastAPI's `Depends()` is used throughout to inject database sessions, current users, and service instances.

### Provider Plugin System

Providers live in `app/services/provider_plugins/`. Each plugin implements a common interface, allowing new providers to be added without modifying existing code or the routing engine.

---

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

---

## Code Quality

```bash
# Linting
ruff check app/

# Auto-fix
ruff check app/ --fix

# Type checking
mypy app/
```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| SQLModel over raw SQLAlchemy | Less boilerplate, Pydantic-native validation |
| AES-256-GCM for API keys | Authenticated encryption — confidentiality + integrity |
| Composite Settings classes | Avoids monolithic BaseSettings god class |
| Channel-based logging | Separate files for app / gateway / provider / request / health |
| Repository pattern | Testable data access, no business logic leaks into ORM |
| Plugin-based providers | Open/Closed principle — extend without modification |

---

## Environment Variables

All configuration is sourced from environment variables or `.env`. See `.env.example` for the full list with defaults.

Key groups: General · Host · CORS · Database · Security · API · Logging · Scheduler · Provider · Notification · Backup · Tray.

---

## License

MIT

