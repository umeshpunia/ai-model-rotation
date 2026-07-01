# AI Gateway Pro — Technical Audit & Issues Report

This document presents a comprehensive list of structural observations, technical issues, and recommendations identified during a full codebase audit of the project.

---

## High-Priority Issues & Gaps

### 1. Hardcoded Streaming Costs in Logger
*   **Location:** `backend/app/services/gateway_service.py` (Line 233)
*   **Description:** In `execute_stream_chat`, the cost of streaming completions is hardcoded to `0.0` inside `_log_request`:
    ```python
    self._log_request(provider.id, key.id, request.model, True, 200, latency_ms, cost=0.0)
    ```
*   **Impact:** Usage and token cost analysis for streaming models will show inaccurate or zero expenditures on the dashboard.
*   **Recommendation:** Implement a stream token counter or parser to approximate input/output usage, or update the cost post-stream calculation once the connection terminates.

### 2. Hardcoded Key Cooldown Timers
*   **Location:** `backend/app/services/gateway_service.py` (Line 149)
*   **Description:** When a provider returns a `429 Rate Limit` error, the key is automatically placed on cooldown for exactly `60` seconds:
    ```python
    key.cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=60)
    ```
*   **Impact:** A fixed 60-second cooldown may be too short or too long depending on the specific rate limits of different tiers and providers.
*   **Recommendation:** Make the cooldown duration configurable via database configurations or environment variables (e.g. `COOLDOWN_DURATION_429`).

---

## Medium-Priority Issues & Maintenance Gaps

### 3. Hardcoded Local URL Configurations in CLI Wrappers
*   **Locations:** 
    *   `aig-claude.bat`
    *   `aig-opencode.bat`
    *   `bin/air-claude.js`
    *   `bin/air-opencode.js`
*   **Description:** The integration CLI wrapper files hardcode `http://localhost:8080/v1` for the proxy endpoint.
*   **Impact:** If the user updates the port settings in `backend/.env` (e.g., to run the gateway on port `9000`), the CLI commands will fail to reach the server.
*   **Recommendation:** Read the host/port dynamically from the `.env` configuration file inside the node wrappers and pass them to the batch processes.

### 4. Lack of Authentication on Gateway API
*   **Locations:** `backend/app/routers/gateway.py`
*   **Description:** The API endpoints under the gateway namespace (e.g. `/v1/chat/completions`, `/v1/messages`) are exposed and do not enforce authentication.
*   **Impact:** While highly convenient for local developer tools, if the gateway service is hosted on a shared network or server, anyone can route requests through your API keys.
*   **Recommendation:** Support optional API Key authentication or client whitelisting for the gateway endpoints, toggleable via environment variables.

---

## Low-Priority & Structural Observations

### 5. SQLite File Locking Limits
*   **Location:** `backend/aigateway.db`
*   **Description:** The application relies on SQLite by default. During schema rebuilds, database upgrades, or active uvicorn operations, the database file becomes locked.
*   **Impact:** Simultaneously running test suites while backend uvicorn is running can cause file lock errors.
*   **Recommendation:** Configure SQLite to use WAL (Write-Ahead Logging) mode, or support quick environment-based migration to a dedicated PostgreSQL database container.

### 6. Smoke Tests Rely on Compiled Binary
*   **Location:** `backend/tests/smoke/test_installer_smoke.py`
*   **Description:** The installer smoke tests are automatically skipped in testing suites because they look for compiled binaries at `backend/backend/dist/aigateway.exe`.
*   **Impact:** Automated CI workflows cannot smoke-test the installer package unless a compilation step is completed beforehand.
*   **Recommendation:** Ensure the PyInstaller task executes as a dependency prior to smoke tests running in CI/CD pipeline definitions.
