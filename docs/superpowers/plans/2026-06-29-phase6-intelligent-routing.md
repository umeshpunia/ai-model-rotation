# Phase 6 Intelligent Routing & Failover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the routing algorithms, dynamic candidate sorting, request proxy logic, key failover rotation rules, stats tracking, and unit tests.

**Architecture:** Create `RoutingEngine` and `GatewayService` inside `backend/app/services/`. Create unit tests simulating API failures to verify rotation rules.

**Tech Stack:** Python 3.12, sqlmodel, httpx

---

### Task 1: Create Routing Engine

**Files:**
- Create: `backend/app/services/routing_engine.py`

- [ ] **Step 1: Write RoutingEngine class**

Write the following code into `backend/app/services/routing_engine.py`:
```python
import random
from typing import List, Tuple, Any
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.entities.model import Model
from app.domain.enums import RoutingMode, KeyStatus, ProviderStatus
from app.repositories.api_key_repository import ApiKeyRepository
from app.core.exceptions import ValidationError

class RoutingEngine:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.key_repo = ApiKeyRepository(session)

    def select_candidates(
        self,
        model_name: str,
        mode: RoutingMode,
        task_type: str | None = None
    ) -> List[Tuple[Provider, ApiKey, Model]]:
        """Find all enabled model/provider/key triplets matching the name and sort them."""
        # Query matching enabled models
        stmt = (
            select(Model, Provider, ApiKey)
            .join(Provider, Model.provider_id == Provider.id)
            .join(ApiKey, ApiKey.provider_id == Provider.id)
            .where(Model.name == model_name)
            .where(Model.is_enabled == True)
            .where(Provider.is_enabled == True)
            .where(Provider.status == ProviderStatus.ENABLED)
            .where(ApiKey.is_enabled == True)
            .where(ApiKey.status != KeyStatus.DISABLED)
            .where(ApiKey.status != KeyStatus.INVALID)
        )
        
        results = self.session.exec(stmt).all()
        triplets = [(r[1], r[2], r[0]) for r in results]
        
        # Filter out keys currently on cooldown
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        usable_triplets = []
        for p, key, m in triplets:
            if key.cooldown_until is None or key.cooldown_until <= now:
                usable_triplets.append((p, key, m))
                
        if not usable_triplets:
            return []
            
        # Apply sorting logic based on the strategy
        if mode == RoutingMode.PRIORITY:
            # Sort first by provider priority (asc), then key priority (asc)
            usable_triplets.sort(key=lambda x: (x[0].priority, x[1].priority))
            
        elif mode == RoutingMode.ROUND_ROBIN:
            # Sort by last_used_at asc (None values first to warm them up)
            usable_triplets.sort(key=lambda x: (x[1].last_used_at is not None, x[1].last_used_at))
            
        elif mode == RoutingMode.LEAST_USED:
            # Sort by usage count asc
            usable_triplets.sort(key=lambda x: x[1].usage_count)
            
        elif mode == RoutingMode.FASTEST:
            # Sort by average latency asc (None values first to warm them up)
            usable_triplets.sort(key=lambda x: (x[1].avg_latency_ms is not None, x[1].avg_latency_ms))
            
        elif mode == RoutingMode.LOWEST_COST:
            # Sort by model cost: input + output cost
            usable_triplets.sort(key=lambda x: (x[2].input_cost_per_1k + x[2].output_cost_per_1k))
            
        elif mode == RoutingMode.HIGHEST_SUCCESS:
            # Sort by success rate descending: success / (usage + 1)
            usable_triplets.sort(key=lambda x: x[1].success_count / (x[1].usage_count + 1), reverse=True)
            
        elif mode == RoutingMode.RANDOM:
            random.shuffle(usable_triplets)
            
        elif mode == RoutingMode.AI_OPTIMIZED:
            # Match task type: sort models supporting task type first
            if task_type:
                usable_triplets.sort(key=lambda x: task_type in x[2].task_types, reverse=True)
            else:
                usable_triplets.sort(key=lambda x: (x[0].priority, x[1].priority))
                
        return usable_triplets
```

- [ ] **Step 2: Commit RoutingEngine**

Run:
```bash
git add backend/app/services/routing_engine.py
git commit -m "feat(services): implement RoutingEngine with multi-strategy sorting logic"
```

---

### Task 2: Create Gateway Proxy Service

**Files:**
- Create: `backend/app/services/gateway_service.py`

- [ ] **Step 1: Write GatewayService class**

Write the following code into `backend/app/services/gateway_service.py`:
```python
import time
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator
from sqlalchemy.orm import Session

from app.domain.entities.request_log import RequestLog
from app.domain.enums import RoutingMode, KeyStatus, HealthStatus
from app.schemas.gateway import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionChunk
from app.services.routing_engine import RoutingEngine
from app.services.api_key_service import ApiKeyService
from app.core.exceptions import UpstreamError, ProviderUnavailableError
from app.core.logging import get_logger

_logger = get_logger("gateway")

class GatewayService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.routing_engine = RoutingEngine(session)
        self.api_key_service = ApiKeyService(session)

    def _log_request(
        self,
        provider_id: int | None,
        key_id: int | None,
        model: str,
        success: bool,
        status_code: int | None,
        latency_ms: float,
        error_msg: str = "",
        cost: float = 0.0,
    ) -> None:
        log = RequestLog(
            provider_id=provider_id,
            api_key_id=key_id,
            model=model,
            task_type="general",
            endpoint="/v1/chat/completions",
            method="POST",
            success=success,
            status_code=status_code,
            latency_ms=latency_ms,
            error_message=error_msg,
            total_cost=cost
        )
        self.session.add(log)
        self.session.flush()

    async def execute_chat(
        self,
        request: ChatCompletionRequest,
        mode: RoutingMode,
        task_type: str | None = None
    ) -> ChatCompletionResponse:
        candidates = self.routing_engine.select_candidates(request.model, mode, task_type)
        if not candidates:
            raise ProviderUnavailableError("No usable providers or API keys available for this model.")

        for provider, key, model_info in candidates:
            start_time = time.perf_counter()
            try:
                # Decrypt raw credential
                raw_key = self.api_key_service.reveal_key(key.id)
                plugin = self.api_key_service.plugin_manager.get_plugin(provider.plugin)
                
                # Execute request
                response = await plugin.chat_completion(raw_key, provider.base_url, request, provider.config)
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                
                # Calculate cost (input_cost_per_1k & output_cost_per_1k)
                prompt_cost = (response.usage.prompt_tokens / 1000.0) * model_info.input_cost_per_1k
                comp_cost = (response.usage.completion_tokens / 1000.0) * model_info.output_cost_per_1k
                total_cost = prompt_cost + comp_cost
                
                # Update key stats on success
                moment = datetime.now(timezone.utc)
                key.last_used_at = moment
                key.last_success_at = moment
                key.success_count += 1
                key.usage_count += 1
                key.consecutive_failures = 0
                key.total_tokens += response.usage.total_tokens
                key.total_cost += total_cost
                key.last_latency_ms = latency_ms
                key.status = KeyStatus.HEALTHY
                key.health_status = HealthStatus.HEALTHY
                
                # Average latency update
                if key.avg_latency_ms is None:
                    key.avg_latency_ms = latency_ms
                else:
                    key.avg_latency_ms = (key.avg_latency_ms * 0.9) + (latency_ms * 0.1)

                self.session.add(key)
                self.session.flush()

                self._log_request(provider.id, key.id, request.model, True, 200, latency_ms, cost=total_cost)
                return response
                
            except UpstreamError as err:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                self._handle_rotation_rules(key, err.status_code, str(err))
                self._log_request(provider.id, key.id, request.model, False, err.status_code, latency_ms, str(err))
                
            except Exception as exc:
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                self._handle_rotation_rules(key, 500, str(exc))
                self._log_request(provider.id, key.id, request.model, False, 500, latency_ms, str(exc))

        raise ProviderUnavailableError("All provider connection candidates were exhausted without success.")

    def _handle_rotation_rules(self, key: ApiKey, status_code: int, error_msg: str) -> None:
        """Evaluate key failover rotation rules."""
        key.last_used_at = datetime.now(timezone.utc)
        key.last_failure_at = datetime.now(timezone.utc)
        key.failure_count += 1
        key.consecutive_failures += 1
        key.last_error = error_msg
        
        if status_code in (401, 403):
            # Auth errors -> disable key permanently until fixed
            key.status = KeyStatus.INVALID
            key.health_status = HealthStatus.UNHEALTHY
            key.is_enabled = False
        elif status_code == 429:
            # Rate limit -> put key on cooldown for 60 seconds
            key.status = KeyStatus.COOLDOWN
            key.health_status = HealthStatus.DEGRADED
            key.cooldown_until = datetime.now(timezone.utc) + timedelta(seconds=60)
        else:
            # Generic 500 or timeout error -> temporary degraded health state
            key.status = KeyStatus.UNKNOWN
            key.health_status = HealthStatus.DEGRADED
            
        self.session.add(key)
        self.session.flush()
```

- [ ] **Step 2: Commit GatewayService**

Run:
```bash
git add backend/app/services/gateway_service.py
git commit -m "feat(services): implement GatewayService proxy completions and failover rotation"
```

---

### Task 3: Create Routing & Failover Unit Tests

**Files:**
- Create: `backend/tests/unit/test_routing.py`

- [ ] **Step 1: Write routing and failover tests**

Write the following code into `backend/tests/unit/test_routing.py`:
```python
import pytest
from datetime import datetime, timezone, timedelta
from app.core.database import session_scope, get_settings, dispose_engine
from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.entities.model import Model
from app.domain.enums import ApiFormat, AuthType, RoutingMode, KeyStatus
from app.services.routing_engine import RoutingEngine
from app.services.gateway_service import GatewayService
from app.schemas.gateway import ChatCompletionRequest, Message
from app.core.exceptions import ProviderUnavailableError
from app.repositories.provider_repository import ProviderRepository
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.model_repository import ModelRepository

@pytest.fixture(autouse=True)
def setup_test_db():
    settings = get_settings()
    original_url = settings.database.database_test_url
    settings.database.database_test_url = "sqlite:///:memory:"
    dispose_engine()
    
    from sqlmodel import SQLModel
    from app.core.database import get_engine
    SQLModel.metadata.create_all(get_engine())
    yield
    SQLModel.metadata.drop_all(get_engine())
    settings.database.database_test_url = original_url
    dispose_engine()

def test_routing_strategies_sorting():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        key_repo = ApiKeyRepository(session)
        model_repo = ModelRepository(session)
        engine = RoutingEngine(session)
        
        provider = Provider(
            name="OpenAI", slug="openai", plugin="openai", api_format=ApiFormat.OPENAI, auth_type=AuthType.BEARER, base_url="https://api.openai.com/v1"
        )
        provider_repo.add(provider)
        
        key1 = ApiKey(provider_id=provider.id, name="Key 1", encrypted_key="enc1", key_hint="hint1", fingerprint="fp1", usage_count=10, priority=1)
        key2 = ApiKey(provider_id=provider.id, name="Key 2", encrypted_key="enc2", key_hint="hint2", fingerprint="fp2", usage_count=2, priority=2)
        key_repo.add(key1)
        key_repo.add(key2)
        
        model = Model(provider_id=provider.id, name="gpt-4o", display_name="GPT-4o")
        model_repo.add(model)
        
        # Test PRIORITY sorting: key1 priority=1 should be first
        candidates_prio = engine.select_candidates("gpt-4o", RoutingMode.PRIORITY)
        assert len(candidates_prio) == 2
        assert candidates_prio[0][1].name == "Key 1"
        
        # Test LEAST_USED sorting: key2 usage=2 should be first
        candidates_usage = engine.select_candidates("gpt-4o", RoutingMode.LEAST_USED)
        assert candidates_usage[0][1].name == "Key 2"

def test_failover_rotation_rules():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        key_repo = ApiKeyRepository(session)
        model_repo = ModelRepository(session)
        
        provider = Provider(
            name="OpenAI", slug="openai", plugin="openai", api_format=ApiFormat.OPENAI, auth_type=AuthType.BEARER, base_url="https://api.openai.com/v1"
        )
        provider_repo.add(provider)
        
        key = ApiKey(provider_id=provider.id, name="Key 1", encrypted_key="enc1", key_hint="hint1", fingerprint="fp1", priority=1)
        key_repo.add(key)
        
        model = Model(provider_id=provider.id, name="gpt-4o", display_name="GPT-4o")
        model_repo.add(model)
        
        service = GatewayService(session)
        
        # Test Auth error (401) rotation rule -> sets Key to INVALID and disables it
        service._handle_rotation_rules(key, 401, "Unauthorized")
        assert key.status == KeyStatus.INVALID
        assert key.is_enabled is False
        
        # Enable it again for cooldown test
        key.is_enabled = True
        key_repo.update(key, {"is_enabled": True})
        
        # Test Rate Limit (429) rotation rule -> sets Key to COOLDOWN
        service._handle_rotation_rules(key, 429, "Too Many Requests")
        assert key.status == KeyStatus.COOLDOWN
        assert key.cooldown_until > datetime.now(timezone.utc)
```

- [ ] **Step 2: Run all unit tests**

Run: `.venv\Scripts\pytest tests/ -v`
Expected output: 28 passed tests.

- [ ] **Step 3: Commit routing tests**

Run:
```bash
git add backend/tests/unit/test_routing.py
git commit -m "test: add routing strategies and failover rotation rule unit tests"
```

---

### Task 4: Update Phase Status Documentation

**Files:**
- Modify: `phase.md`

- [ ] **Step 1: Check off Phase 6 checkboxes**

Change checkboxes in `d:\projects\python\ai-model-rotation\phase.md` lines 126-149 under `## Phase 6: Intelligent Routing & Failover` to `[x]`.

- [ ] **Step 2: Update Phase 6 summary status**

Change:
```markdown
| 6 | Intelligent Routing & Failover | Not Started |
```
To:
```markdown
| 6 | Intelligent Routing & Failover | Complete |
```

- [ ] **Step 3: Commit phase tracking updates**

Run:
```bash
git add phase.md docs/superpowers/plans/2026-06-29-phase6-intelligent-routing.md docs/superpowers/specs/2026-06-29-phase6-intelligent-routing-design.md
git commit -m "docs: complete Phase 6 routing and failover status tracking and specs/plans"
```
