# Phase 5 API Key Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the secure API Key CRUD service, credential encryption at rest, live key validation, masking, health tracking, and unit tests.

**Architecture:** Create the `ApiKeyService` class using `EncryptionService` for cryptographic actions and `ApiKeyRepository` for persistence. Create unit tests verifying key lifecycles.

**Tech Stack:** Python 3.12, sqlmodel, cryptography

---

### Task 1: Create API Key Service

**Files:**
- Create: `backend/app/services/api_key_service.py`

- [ ] **Step 1: Write ApiKeyService class**

Write the following code into `backend/app/services/api_key_service.py`:
```python
import hashlib
import json
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.domain.entities.api_key import ApiKey
from app.domain.enums import KeyStatus, HealthStatus
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.provider_repository import ProviderRepository
from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate, ApiKeyTestResult
from app.core.security import EncryptionService, EncryptedBlob
from app.core.exceptions import ValidationError, NotFoundError
from app.services.provider_plugins.manager import get_plugin_manager

class ApiKeyService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = ApiKeyRepository(session)
        self.provider_repo = ProviderRepository(session)
        self.encryption_service = EncryptionService()
        self.plugin_manager = get_plugin_manager()

    def _get_fingerprint(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def create_key(self, key_in: ApiKeyCreate) -> ApiKey:
        # Deduplication check
        fingerprint = self._get_fingerprint(key_in.key)
        existing = self.repo.get_by_fingerprint(key_in.provider_id, fingerprint)
        if existing:
            raise ValidationError("This API key is already registered for this provider.")

        # Encrypt the raw key
        blob = self.encryption_service.encrypt(key_in.key)
        encrypted_key_str = json.dumps(blob.to_dict())
        key_hint = self.encryption_service.mask_key(key_in.key)

        # Create model instance
        key_model = ApiKey(
            provider_id=key_in.provider_id,
            name=key_in.name,
            encrypted_key=encrypted_key_str,
            key_hint=key_hint,
            fingerprint=fingerprint,
            priority=key_in.priority,
            is_enabled=key_in.is_enabled,
            expires_at=key_in.expires_at,
            status=KeyStatus.UNKNOWN,
            health_status=HealthStatus.UNKNOWN
        )
        self.repo.add(key_model)
        return key_model

    def update_key(self, key_id: int, key_in: ApiKeyUpdate) -> ApiKey:
        key_model = self.repo.get_or_404(key_id)
        update_data = key_in.model_dump(exclude_unset=True)

        if "key" in update_data and update_data["key"] is not None:
            raw_key = update_data.pop("key")
            # Deduplication check
            fingerprint = self._get_fingerprint(raw_key)
            existing = self.repo.get_by_fingerprint(key_model.provider_id, fingerprint)
            if existing and existing.id != key_model.id:
                raise ValidationError("This API key is already registered for this provider.")

            blob = self.encryption_service.encrypt(raw_key)
            update_data["encrypted_key"] = json.dumps(blob.to_dict())
            update_data["key_hint"] = self.encryption_service.mask_key(raw_key)
            update_data["fingerprint"] = fingerprint

        self.repo.update(key_model, update_data)
        return key_model

    def delete_key(self, key_id: int) -> None:
        key_model = self.repo.get_or_404(key_id)
        self.repo.delete(key_model)

    def reveal_key(self, key_id: int) -> str:
        key_model = self.repo.get_or_404(key_id)
        blob_dict = json.loads(key_model.encrypted_key)
        blob = EncryptedBlob.from_dict(blob_dict)
        return self.encryption_service.decrypt(blob)

    async def test_key(self, key_id: int) -> ApiKeyTestResult:
        key_model = self.repo.get_or_404(key_id)
        provider = self.provider_repo.get_or_404(key_model.provider_id)
        
        # Decrypt raw API key credential
        raw_key = self.reveal_key(key_id)
        
        plugin = self.plugin_manager.get_plugin(provider.plugin)
        
        start_time = time.perf_counter()
        success = False
        status_code = None
        message = ""
        
        try:
            success = await plugin.test_connection(raw_key, provider.base_url, provider.config)
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            status_code = 200 if success else 400
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            message = str(e)
        
        # Update key health statistics
        moment = datetime.now(timezone.utc)
        key_model.last_used_at = moment
        key_model.last_latency_ms = latency_ms
        
        if success:
            key_model.status = KeyStatus.HEALTHY
            key_model.health_status = HealthStatus.HEALTHY
            key_model.last_success_at = moment
            key_model.success_count += 1
            key_model.consecutive_failures = 0
            key_model.last_error = ""
        else:
            key_model.status = KeyStatus.INVALID
            key_model.health_status = HealthStatus.UNHEALTHY
            key_model.last_failure_at = moment
            key_model.failure_count += 1
            key_model.consecutive_failures += 1
            key_model.last_error = message or "Connection test failed."
            
        # Update average latency
        if key_model.avg_latency_ms is None:
            key_model.avg_latency_ms = latency_ms
        else:
            # Simple moving average (0.1 weight on new latency)
            key_model.avg_latency_ms = (key_model.avg_latency_ms * 0.9) + (latency_ms * 0.1)
            
        self.session.add(key_model)
        self.session.flush()
        
        return ApiKeyTestResult(
            api_key_id=key_id,
            success=success,
            status=key_model.status,
            latency_ms=latency_ms,
            status_code=status_code,
            message=key_model.last_error
        )
```

- [ ] **Step 2: Commit ApiKeyService**

Run:
```bash
git add backend/app/services/api_key_service.py
git commit -m "feat(services): implement ApiKeyService secure CRUD operations and validation tests"
```

---

### Task 2: Create API Key Service Tests

**Files:**
- Create: `backend/tests/unit/test_keys.py`

- [ ] **Step 1: Write test suite**

Write the following code into `backend/tests/unit/test_keys.py`:
```python
import pytest
from app.core.database import session_scope, get_settings, dispose_engine
from app.services.api_key_service import ApiKeyService
from app.repositories.provider_repository import ProviderRepository
from app.domain.entities.provider import Provider
from app.domain.enums import ApiFormat, AuthType, KeyStatus
from app.schemas.api_key import ApiKeyCreate, ApiKeyUpdate
from app.core.exceptions import ValidationError

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

def test_api_key_lifecycle_and_encryption():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        service = ApiKeyService(session)
        
        provider = Provider(
            name="OpenAI Provider",
            slug="openai",
            plugin="openai",
            api_format=ApiFormat.OPENAI,
            auth_type=AuthType.BEARER,
            base_url="https://api.openai.com/v1"
        )
        provider_repo.add(provider)
        
        # Test creation & encryption
        create_payload = ApiKeyCreate(
            provider_id=provider.id,
            name="Main Key",
            key="sk-proj-super-secret-key-material-here"
        )
        key_rec = service.create_key(create_payload)
        assert key_rec.id is not None
        assert key_rec.key_hint.startswith("sk-p")
        assert "super-secret" not in key_rec.encrypted_key  # encrypted opaque JSON blob
        
        # Test decryption/reveal
        decrypted = service.reveal_key(key_rec.id)
        assert decrypted == "sk-proj-super-secret-key-material-here"
        
        # Test duplicate verification (should raise ValidationError)
        with pytest.raises(ValidationError):
            service.create_key(create_payload)

        # Test update without changing credential
        update_payload = ApiKeyUpdate(name="Renamed Key", priority=50)
        updated = service.update_key(key_rec.id, update_payload)
        assert updated.name == "Renamed Key"
        assert updated.priority == 50
        assert service.reveal_key(key_rec.id) == "sk-proj-super-secret-key-material-here"

        # Test delete
        service.delete_key(key_rec.id)
        assert service.repo.get(key_rec.id) is None
```

- [ ] **Step 2: Run all unit tests**

Run: `.venv\Scripts\pytest tests/ -v`
Expected output: 26 passed tests.

- [ ] **Step 3: Commit unit tests**

Run:
```bash
git add backend/tests/unit/test_keys.py
git commit -m "test: add ApiKeyService lifecycle and decryption unit tests"
```

---

### Task 3: Update Phase Status Documentation

**Files:**
- Modify: `phase.md`

- [ ] **Step 1: Check off Phase 5 checkboxes**

Change checkboxes in `d:\projects\python\ai-model-rotation\phase.md` lines 103-125 under `## Phase 5: API Key Management` to `[x]`.

- [ ] **Step 2: Update Phase 5 summary status**

Change:
```markdown
| 5 | API Key Management | Not Started |
```
To:
```markdown
| 5 | API Key Management | Complete |
```

- [ ] **Step 3: Commit phase tracking updates**

Run:
```bash
git add phase.md docs/superpowers/plans/2026-06-29-phase5-api-key-management.md docs/superpowers/specs/2026-06-29-phase5-api-key-management-design.md
git commit -m "docs: complete Phase 5 API key management status tracking and specs/plans"
```
