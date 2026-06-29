# Phase 3 Data Layer Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement comprehensive unit tests for the Data Layer ORM entities, relationships, CRUD repositories, Pydantic DTO schemas, and Alembic migrations.

**Architecture:** Create test modules under `tests/unit/` using transactional session fixtures mapped to an in-memory SQLite backend, run verification using pytest, and check off Phase 3 tasks in `phase.md`.

**Tech Stack:** pytest, Python 3.12, SQLModel, Alembic

---

### Task 1: Create Database Models and Relationship Tests

**Files:**
- Create: `tests/unit/test_models.py`

- [ ] **Step 1: Write model unit tests**

Write the following code into `tests/unit/test_models.py`:
```python
import pytest
from sqlalchemy import text
from sqlmodel import select
from app.core.database import session_scope, get_settings, dispose_engine
from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.entities.model import Model
from app.domain.entities.user import User
from app.domain.enums import ApiFormat, AuthType, ProviderStatus, ApiKeyStatus, UserRole

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

def test_provider_creation_and_defaults():
    with session_scope() as session:
        provider = Provider(
            name="OpenAI Provider",
            slug="openai",
            plugin="openai_plugin",
            api_format=ApiFormat.OPENAI,
            auth_type=AuthType.BEARER,
            base_url="https://api.openai.com/v1"
        )
        session.add(provider)
        session.flush()
        
        assert provider.id is not None
        assert provider.status == ProviderStatus.ENABLED
        assert provider.is_enabled is True
        assert provider.priority == 100

def test_provider_key_and_model_relationships():
    with session_scope() as session:
        provider = Provider(
            name="Gemini Provider",
            slug="gemini",
            plugin="gemini_plugin",
            api_format=ApiFormat.GEMINI,
            auth_type=AuthType.API_KEY,
            base_url="https://generativelanguage.googleapis.com"
        )
        session.add(provider)
        session.flush()
        
        key = ApiKey(
            provider_id=provider.id,
            name="Gemini Primary Key",
            key_ciphertext="encrypted-key-blob-nonce",
            priority=10
        )
        model = Model(
            provider_id=provider.id,
            name="Gemini 1.5 Flash",
            slug="gemini-1.5-flash",
            context_window=1000000,
            pricing_input_million=0.075,
            pricing_output_million=0.30
        )
        session.add_all([key, model])
        session.flush()
        session.refresh(provider)
        
        assert len(provider.api_keys) == 1
        assert provider.api_keys[0].name == "Gemini Primary Key"
        assert len(provider.models) == 1
        assert provider.models[0].slug == "gemini-1.5-flash"

def test_cascade_deletion():
    with session_scope() as session:
        provider = Provider(
            name="Anthropic Provider",
            slug="anthropic",
            plugin="anthropic_plugin",
            api_format=ApiFormat.ANTHROPIC,
            auth_type=AuthType.CUSTOM_HEADER,
            base_url="https://api.anthropic.com"
        )
        session.add(provider)
        session.flush()
        
        key = ApiKey(
            provider_id=provider.id,
            name="Claude Primary Key",
            key_ciphertext="encrypted-key",
            priority=10
        )
        session.add(key)
        session.flush()
        
        provider_id = provider.id
        key_id = key.id
        
        # Verify both exist
        assert session.get(Provider, provider_id) is not None
        assert session.get(ApiKey, key_id) is not None
        
        # Delete provider and check cascade delete on ApiKey
        session.delete(provider)
        session.flush()
        
        assert session.get(Provider, provider_id) is None
        assert session.get(ApiKey, key_id) is None

def test_user_creation():
    with session_scope() as session:
        user = User(
            username="admin",
            email="[email protected]",
            hashed_password="hashed_bcrypt_password_here",
            role=UserRole.ADMIN
        )
        session.add(user)
        session.flush()
        
        assert user.id is not None
        assert user.is_active is True
```

- [ ] **Step 2: Run model tests**

Run: `.venv\Scripts\pytest tests/unit/test_models.py -v`
Expected output: 4 passed tests.

- [ ] **Step 3: Commit model tests**

Run:
```bash
git add tests/unit/test_models.py
git commit -m "test: add database ORM models unit tests"
```

---

### Task 2: Create Repository CRUD Tests

**Files:**
- Create: `tests/unit/test_repositories.py`

- [ ] **Step 1: Write repository unit tests**

Write the following code into `tests/unit/test_repositories.py`:
```python
import pytest
from app.core.database import session_scope, get_settings, dispose_engine
from app.repositories.provider_repository import ProviderRepository
from app.repositories.api_key_repository import ApiKeyRepository
from app.repositories.user_repository import UserRepository
from app.domain.entities.provider import Provider
from app.domain.entities.api_key import ApiKey
from app.domain.entities.user import User
from app.domain.enums import ApiFormat, AuthType, ApiKeyStatus

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

def test_base_repository_crud():
    with session_scope() as session:
        repo = ProviderRepository(session)
        
        # Test Create / Add
        provider = Provider(
            name="OpenAI Provider",
            slug="openai",
            plugin="openai_plugin",
            api_format=ApiFormat.OPENAI,
            auth_type=AuthType.BEARER,
            base_url="https://api.openai.com/v1"
        )
        repo.add(provider)
        
        provider_id = provider.id
        assert provider_id is not None
        
        # Test Read / Get
        fetched = repo.get(provider_id)
        assert fetched is not None
        assert fetched.slug == "openai"
        
        # Test Update
        repo.update(fetched, {"name": "OpenAI Enterprise"})
        refetched = repo.get(provider_id)
        assert refetched.name == "OpenAI Enterprise"
        
        # Test List / Count
        providers = repo.list()
        assert len(providers) == 1
        assert repo.count() == 1
        
        # Test Paginate
        items, total = repo.paginate(offset=0, limit=10)
        assert len(items) == 1
        assert total == 1
        
        # Test Delete
        repo.delete(refetched)
        assert repo.get(provider_id) is None

def test_specific_repository_helpers():
    with session_scope() as session:
        provider_repo = ProviderRepository(session)
        key_repo = ApiKeyRepository(session)
        user_repo = UserRepository(session)
        
        provider = Provider(
            name="Gemini Provider",
            slug="gemini",
            plugin="gemini_plugin",
            api_format=ApiFormat.GEMINI,
            auth_type=AuthType.API_KEY,
            base_url="https://generativelanguage.googleapis.com"
        )
        provider_repo.add(provider)
        
        key = ApiKey(
            provider_id=provider.id,
            name="Key Active",
            key_ciphertext="cipher-active",
            status=ApiKeyStatus.HEALTHY,
            is_enabled=True,
            priority=1
        )
        key_disabled = ApiKey(
            provider_id=provider.id,
            name="Key Disabled",
            key_ciphertext="cipher-disabled",
            status=ApiKeyStatus.DISABLED,
            is_enabled=False,
            priority=2
        )
        key_repo.add(key)
        key_repo.add(key_disabled)
        
        # Test ApiKeyRepository helper to fetch active keys for provider
        active_keys = key_repo.get_active_keys_for_provider(provider.id)
        assert len(active_keys) == 1
        assert active_keys[0].name == "Key Active"
        
        # Test UserRepository helper to fetch by username
        user = User(
            username="umesh",
            email="[email protected]",
            hashed_password="hashed_password",
        )
        user_repo.add(user)
        
        fetched_user = user_repo.get_by_username("umesh")
        assert fetched_user is not None
        assert fetched_user.email == "[email protected]"
        
        assert user_repo.get_by_username("nonexistent") is None
```

- [ ] **Step 2: Run repository tests**

Run: `.venv\Scripts\pytest tests/unit/test_repositories.py -v`
Expected output: 2 passed tests.

- [ ] **Step 3: Commit repository tests**

Run:
```bash
git add tests/unit/test_repositories.py
git commit -m "test: add generic and entity repositories unit tests"
```

---

### Task 3: Create DTO Schemas Validation Tests

**Files:**
- Create: `tests/unit/test_schemas.py`

- [ ] **Step 1: Write schema unit tests**

Write the following code into `tests/unit/test_schemas.py`:
```python
import pytest
from pydantic import ValidationError
from app.schemas.user import UserCreate
from app.schemas.provider import ProviderCreate
from app.domain.enums import ApiFormat, AuthType

def test_user_schema_validation():
    # Valid input
    user = UserCreate(
        username="john_doe",
        email="[email protected]",
        password="securepassword123"
    )
    assert user.username == "john_doe"
    
    # Invalid email
    with pytest.raises(ValidationError):
        UserCreate(
            username="john_doe",
            email="not-an-email",
            password="securepassword123"
        )

def test_provider_schema_validation():
    # Valid input
    provider = ProviderCreate(
        name="Grok Provider",
        slug="grok",
        plugin="grok_plugin",
        api_format=ApiFormat.OPENAI,
        auth_type=AuthType.BEARER,
        base_url="https://api.x.ai/v1"
    )
    assert provider.slug == "grok"
    
    # Missing required field base_url
    with pytest.raises(ValidationError):
        ProviderCreate(
            name="Grok Provider",
            slug="grok",
            plugin="grok_plugin",
            api_format=ApiFormat.OPENAI,
            auth_type=AuthType.BEARER
        )
```

- [ ] **Step 2: Run schema tests**

Run: `.venv\Scripts\pytest tests/unit/test_schemas.py -v`
Expected output: 2 passed tests.

- [ ] **Step 3: Commit schema tests**

Run:
```bash
git add tests/unit/test_schemas.py
git commit -m "test: add pydantic schema validation tests"
```

---

### Task 4: Create Alembic Migrations Verification Test

**Files:**
- Create: `tests/unit/test_migrations.py`

- [ ] **Step 1: Write migration verification test**

Write the following code into `tests/unit/test_migrations.py`:
```python
import os
import pytest
from alembic.config import Config
from alembic import command
from app.core.config import get_settings
from app.core.database import dispose_engine

def test_alembic_upgrade_downgrade():
    settings = get_settings()
    original_url = settings.database.database_test_url
    # Use a temporary SQLite database file for testing migration upgrade/downgrade
    db_file = "test_migration_run.db"
    settings.database.database_test_url = f"sqlite:///{db_file}"
    dispose_engine()
    
    try:
        # Load Alembic configuration and point it to the python root CWD
        alembic_cfg = Config("alembic.ini")
        
        # Run upgrade head
        command.upgrade(alembic_cfg, "head")
        
        # Run downgrade back to base
        command.downgrade(alembic_cfg, "base")
    finally:
        # Clean up database file
        dispose_engine()
        if os.path.exists(db_file):
            os.remove(db_file)
        # Restore settings
        settings.database.database_test_url = original_url
        dispose_engine()
```

- [ ] **Step 2: Run migration tests**

Run: `.venv\Scripts\pytest tests/unit/test_migrations.py -v`
Expected output: 1 passed test.

- [ ] **Step 3: Run all unit tests**

Run: `.venv\Scripts\pytest tests/ -v`
Expected output: 24 passed tests.

- [ ] **Step 4: Commit migration tests**

Run:
```bash
git add tests/unit/test_migrations.py
git commit -m "test: add alembic database migrations execution unit test"
```

---

### Task 5: Update Phase Status Documentation

**Files:**
- Modify: `phase.md`

- [ ] **Step 1: Update phase.md checkboxes**

Edit `d:\projects\python\ai-model-rotation\phase.md` lines 55-84.
Change all checkboxes under `## Phase 3: Data Layer` to `[x]`.

- [ ] **Step 2: Update Phase 3 summary status**

Edit `d:\projects\python\ai-model-rotation\phase.md` line 353.
Change:
```markdown
| 3 | Data Layer | Not Started |
```
To:
```markdown
| 3 | Data Layer | Complete |
```

- [ ] **Step 3: Commit phase tracking updates**

Run:
```bash
git add phase.md docs/superpowers/plans/2026-06-29-phase3-data-tests.md docs/superpowers/specs/2026-06-29-phase3-data-tests-design.md
git commit -m "docs: complete Phase 3 data layer tracking and specs/plans"
```
Expected output: Commit completed.
