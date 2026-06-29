# Design Specification: Phase 8 REST API

## 1. Goal
Design and bootstrap the FastAPI web application, API versioning prefixes (`/api/v1` for admin management and `/v1` for the proxy gateway), authentication/authorization middlewares, and all required router endpoints.

## 2. Requirements & Scope
- **Bootstrapping**: Create `backend/app/main.py` configuring startup/shutdown hooks, global exception handlers, CORS headers, logging trace middleware, and rate limiting.
- **Middlewares & Security**:
  - JWT verification dependency (`get_current_user`).
  - Role-based access control checking (`require_role(role)`).
  - Rate limiting mapping per client IP/API key.
- **Admin/Management Routing (`/api/v1`)**:
  - `/auth`: login and token refresh.
  - `/providers`: CRUD + connection test.
  - `/keys`: CRUD + encryption + connection test + rotation.
  - `/models`: list models.
  - `/settings`: configuration profile import/export.
  - `/health` & `/status`: diagnostic states.
  - `/statistics`: query `Statistic` history.
  - `/logs`: paginated `RequestLog` views.
  - `/notifications`: manage alerts history.
- **Gateway Proxy Routing (`/v1`)**:
  - `POST /v1/chat/completions`: proxy to `GatewayService` (supporting completions and streaming).

## 3. Design Details

### A. Directory Layout
```
backend/app/
  ├── main.py (FastAPI bootstrap & lifespan)
  ├── middleware/
  │     ├── logging.py (request/tracing logging)
  │     └── rate_limit.py (in-memory rate limiter)
  ├── routers/
  │     ├── __init__.py (prefix registration)
  │     ├── auth.py
  │     ├── providers.py
  │     ├── keys.py
  │     ├── gateway.py
  │     ├── health.py
  │     └── ...
```

### B. Gateway completions proxy streaming details
For streaming request payloads (i.e. `stream: true`), the endpoint will return a FastAPI `StreamingResponse` wrapping an asynchronous generator that yields chunked lines in standard SSE format (`data: {...}\n\n`).

### C. Seeding Admin User on Startup
If `users` database table is empty during startup, the server automatically inserts a default admin user:
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `admin`
- **Is Active / Superuser**: `True`
