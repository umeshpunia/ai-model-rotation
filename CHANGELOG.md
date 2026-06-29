# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Frontend dashboard scaffolding (Phase 11 — in progress)

---

## [0.10.0] - 2026-06-29

### Added
- **Configuration Profiles**: Settings CRUD via REST API with profile support (Development, Production, Testing).
- **Backup System**: Manual and scheduled database backups with ZIP compression, rolling retention, and full restore capability.
- **Configuration Hot-Reload**: Dynamic settings propagation to running scheduler and background services without restart.
- Backups REST API endpoints (`GET`, `POST`, `DELETE`, `POST /restore`).
- Unit tests for backup create, delete, restore lifecycle.

---

## [0.9.0] - 2026-06-29

### Added
- **Notification System**: Multi-channel notification dispatcher with Desktop, Email (SMTP), Slack, Discord, Telegram, and Webhook integrations.
- Notification persistence and history via database storage.
- Gateway triggers for key status changes, cooldowns, provider offline/recovery, and quota events.
- Legacy REST API aliases under `/v1` namespace for compliance with specification.

---

## [0.8.0] - 2026-06-29

### Added
- **REST API Layer**: Full CRUD endpoints for providers, API keys, models, settings, health, statistics, logs, and notifications.
- JWT-based authentication with role-based access control (Admin, User, Viewer).
- Pagination, filtering, and sorting for all list endpoints.
- Interactive API documentation via Swagger UI and ReDoc.

---

## [0.7.0] - 2026-06-29

### Added
- **Background Services & Health Monitoring**: APScheduler-based background jobs for health checks, statistics aggregation, log cleanup, notification cleanup, and database backups.
- Automatic provider and key health recovery when connectivity is restored.

---

## [0.6.0] - 2026-06-29

### Added
- **Intelligent Routing & Failover**: Configurable routing strategies (Priority, Round Robin, Least Used, Fastest, Lowest Cost, Highest Success, Random, AI-Optimized).
- Automatic key rotation on 401, 403, 429, timeout, and server errors.
- Provider failover chains with automatic fallback across multiple providers.

---

## [0.5.0] - 2026-06-29

### Added
- **API Key Management**: Unlimited API keys per provider with AES-256-GCM encryption at rest.
- Key lifecycle tracking (status, priority, usage, failures, cooldown, latency, health statistics).

---

## [0.4.0] - 2026-06-29

### Added
- **Provider Plugin System**: Dynamic provider loading with a common interface.
- Built-in plugins for OpenAI, Anthropic, Google Gemini, Grok, DeepSeek, OpenRouter, Ollama, and Azure OpenAI.
- Adding a new provider requires no modification of existing provider implementations.

---

## [0.3.0] - 2026-06-29

### Added
- **Data Layer**: SQLModel entities, Alembic migration support, repository pattern for all domain models.
- Automatic database creation and schema management.

---

## [0.2.0] - 2026-06-29

### Added
- **Core Infrastructure**: Configuration management (JSON, env vars, database), structured logging with channel-based file rotation, security utilities (JWT, bcrypt, AES encryption), exception handling framework.

---

## [0.1.0] - 2026-06-29

### Added
- **Foundation & Architecture**: Initial project scaffolding with clean architecture separation (presentation, business logic, infrastructure, persistence).
- FastAPI application factory with middleware stack (CORS, request logging, error handling).
- Project structure and dependency management via `pyproject.toml`.
