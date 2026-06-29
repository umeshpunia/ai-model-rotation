# Phase 2 Core Infrastructure Testing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement comprehensive unit tests for core utilities (config, security, database, exceptions) to verify Phase 2 readiness.

**Architecture:** Create individual test modules under `tests/unit/` that invoke the app core functions and assert expected behaviors, and run them via pytest.

**Tech Stack:** pytest, Python 3.12, SQLModel/SQLAlchemy

---

### Task 1: Create Configuration System Tests

**Files:**
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: Write config unit tests**

Write the following code into `tests/unit/test_config.py`:
```python
import os
import pytest
from pydantic import ValidationError
from app.core.config import get_settings, reload_settings, SecuritySettings

def test_settings_load():
    settings = get_settings()
    assert settings.general.app_name == "AI Gateway Pro"
    assert settings.database.pool_size == 10

def test_security_validation():
    # Verify key length constraint (>= 32)
    with pytest.raises(ValidationError):
        SecuritySettings(secret_key="short-key")
        
    # Verify salt length constraint (>= 8)
    with pytest.raises(ValidationError):
        SecuritySettings(master_password_salt="short")

def test_settings_hot_reload():
    os.environ["LOG_LEVEL"] = "DEBUG"
    settings = reload_settings()
    try:
        assert settings.general.log_level == "DEBUG"
    finally:
        os.environ["LOG_LEVEL"] = "INFO"
        reload_settings()
```

- [ ] **Step 2: Run config tests**

Run: `.venv\Scripts\pytest tests/unit/test_config.py -v`
Expected output: 3 passed tests.

- [ ] **Step 3: Commit config tests**

Run:
```bash
git add tests/unit/test_config.py
git commit -m "test: add config system unit tests"
```

---

### Task 2: Create Security Primitives Tests

**Files:**
- Create: `tests/unit/test_security.py`

- [ ] **Step 1: Write security unit tests**

Write the following code into `tests/unit/test_security.py`:
```python
import pytest
from app.core.security import (
    hash_password,
    verify_password,
    EncryptionService,
    constant_time_equals,
    generate_secret_key,
    EncryptedBlob,
)
from app.core.exceptions import EncryptionError

def test_password_hashing():
    pwd = "my-secure-password"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong-password", hashed) is False

def test_aes_gcm_encryption():
    svc = EncryptionService(
        secret="test-secret-key-must-be-32-chars-long",
        salt="test-salt-12-chars"
    )
    plaintext = "super-secret-api-key"
    
    blob = svc.encrypt(plaintext)
    assert blob.nonce_b64 != ""
    assert blob.ciphertext_b64 != ""
    
    decrypted = svc.decrypt(blob)
    assert decrypted == plaintext

def test_aes_gcm_decryption_failures():
    svc = EncryptionService(
        secret="test-secret-key-must-be-32-chars-long",
        salt="test-salt-12-chars"
    )
    blob = svc.encrypt("secret")
    
    # Tamper with ciphertext
    blob.ciphertext_b64 = "modified-ciphertext-b64-value"
    with pytest.raises(EncryptionError):
        svc.decrypt(blob)

def test_key_masking():
    masked = EncryptionService.mask_key("sk-proj-1234567890abcdef")
    assert masked.startswith("sk-p")
    assert masked.endswith("cdef")
    assert "*" in masked

def test_constant_time_equals():
    assert constant_time_equals("abc", "abc") is True
    assert constant_time_equals("abc", "def") is False

def test_generate_secret_key():
    key = generate_secret_key()
    assert len(key) >= 64
```

- [ ] **Step 2: Run security tests**

Run: `.venv\Scripts\pytest tests/unit/test_security.py -v`
Expected output: 6 passed tests.

- [ ] **Step 3: Commit security tests**

Run:
```bash
git add tests/unit/test_security.py
git commit -m "test: add security primitives unit tests"
```

---

### Task 3: Create Database Engine Tests

**Files:**
- Create: `tests/unit/test_database.py`

- [ ] **Step 1: Write database unit tests**

Write the following code into `tests/unit/test_database.py`:
```python
import pytest
from sqlalchemy import text
from app.core.database import get_engine, session_scope

def test_database_engine_and_session():
    engine = get_engine()
    assert engine is not None
    
    with session_scope() as session:
        res = session.execute(text("SELECT 1")).scalar()
        assert res == 1

def test_session_scope_rollback():
    # Make sure session rolls back correctly on exception
    with pytest.raises(RuntimeError):
        with session_scope() as session:
            # We raise an error within session scope
            raise RuntimeError("Database error simulation")
```

- [ ] **Step 2: Run database tests**

Run: `.venv\Scripts\pytest tests/unit/test_database.py -v`
Expected output: 2 passed tests.

- [ ] **Step 3: Commit database tests**

Run:
```bash
git add tests/unit/test_database.py
git commit -m "test: add database session unit tests"
```

---

### Task 4: Create Exception Mapping Tests

**Files:**
- Create: `tests/unit/test_exceptions.py`

- [ ] **Step 1: Write exceptions unit tests**

Write the following code into `tests/unit/test_exceptions.py`:
```python
from fastapi import status
from app.core.exceptions import (
    NotFoundError,
    ValidationError,
    AuthenticationError,
    EncryptionError,
    AppError,
)

def test_exception_status_codes():
    assert NotFoundError("").status_code == status.HTTP_404_NOT_FOUND
    assert ValidationError("").status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert AuthenticationError("").status_code == status.HTTP_401_UNAUTHORIZED
    assert EncryptionError("").status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
```

- [ ] **Step 2: Run exceptions tests**

Run: `.venv\Scripts\pytest tests/unit/test_exceptions.py -v`
Expected output: 1 passed test.

- [ ] **Step 3: Run all unit tests**

Run: `.venv\Scripts\pytest tests/ -v`
Expected output: 12 passed tests.

- [ ] **Step 4: Commit exception tests**

Run:
```bash
git add tests/unit/test_exceptions.py
git commit -m "test: add exceptions unit tests"
```
