# Design Specification: Phase 6 Intelligent Routing & Failover

## 1. Goal
Design and implement the core routing engine (`RoutingEngine`) and executing proxy service (`GatewayService`) for AI Gateway Pro. The system must support dynamic, configurable sorting strategies (Priority, Round-Robin, Least-Used, Fastest, Lowest-Cost, Highest-Success, Random, AI-Optimized), handle automatic key rotation/cooldown upon failures (401, 403, 429, 500, 503, timeouts), and track token usage/costs.

## 2. Requirements & Scope
- **Configurable Routing Strategies**:
  - Evaluate enabled Models matching the request.
  - Fetch active/usable API Keys (enabled, status != disabled/invalid, and not currently in cooldown).
  - Sort candidates using:
    - **Priority**: Provider priority asc, then Key priority asc.
    - **Round-Robin**: Sort by `last_used_at` asc.
    - **Least-Used**: Sort by `usage_count` asc.
    - **Fastest**: Sort by `avg_latency_ms` asc.
    - **Lowest-Cost**: Sort by input+output token cost.
    - **Highest-Success**: Sort by success rate descending.
    - **Random**: Shuffle candidates.
    - **AI-Optimized**: Match against `Model.task_types` suited for request type.
- **Failover Logic**:
  - Capture HTTP errors and apply rules:
    - 401/403: Disable key (set status = INVALID). Retry next candidate.
    - 429: Cooldown key (set status = COOLDOWN, cooldown_until = now + backoff). Retry next candidate.
    - 500/Timeout/Server error: Try next key or provider with exponential backoff.
- **Usage Tracking**:
  - Update Key and Provider usage statistics (`usage_count`, `success_count`, `failure_count`, `total_tokens`, `total_cost`, `latency_ms`).

## 3. Design Details

### A. Routing Engine (`services/routing_engine.py`)
- Resolves routing mode: Header `X-Routing-Strategy` > Database settings > default config.
- Implements:
  ```python
  class RoutingEngine:
      def get_candidates(self, session, model_name: str, mode: RoutingMode, task_type: str | None = None) -> list[tuple[Provider, ApiKey, Model]]:
          # Query models -> providers -> usable keys
          # Sort based on RoutingMode
  ```

### B. Gateway Service (`services/gateway_service.py`)
- Loops through candidates, invokes the appropriate plugin's completion or stream execution.
- Intercepts exceptions, calls `handle_failure(key_id, error_code)` to mark state, and continues loop.
- Records request logs using `RequestLog` entity.

## 4. Verification Plan
- **Unit Tests (`tests/unit/test_routing.py`)**:
  - Verify Priority, Least-Used, Lowest-Cost sorting functions.
  - Verify Round-Robin cycling.
  - Mock connection failures and assert that `GatewayService` rotates keys and correctly marks 401 as INVALID and 429 as COOLDOWN.
