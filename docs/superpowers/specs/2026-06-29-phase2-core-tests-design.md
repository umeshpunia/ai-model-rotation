# Design Specification: Phase 2 Core Infrastructure Verification & Testing

## 1. Goal
Provide a comprehensive test suite for Phase 2 (Core Infrastructure) utilities of the AI Gateway Pro backend. This ensures configuration, security, database transactional lifecycles, and exceptions are validated and working according to specs before proceeding with database entities.

## 2. Requirements & Scope
- **Test Coverage**: Design and implement unit tests covering:
  - `app/core/config.py`
  - `app/core/security.py`
  - `app/core/database.py`
  - `app/core/exceptions.py`
- **Validation**: Verify that:
  - Encryption and decryption work securely using AES-256-GCM.
  - Secret key and salt length rules are enforced.
  - Transactions auto-commit and auto-rollback properly.
  - Exceptions map to proper HTTP status codes.

## 3. Design Details

### A. Configuration Tests (`test_config.py`)
Validate the Pydantic-based configuration system:
- Assert that `get_settings()` yields expected structure and default values.
- Force `ValidationError` by initializing `SecuritySettings` with short secret keys (<32 chars) or salts (<8 chars).
- Programmatically modify environment variables, call `reload_settings()`, and verify values update.

### B. Security Primitives Tests (`test_security.py`)
Validate cryptography and auth:
- Test that hashing a password produces a string that matches via `verify_password()`.
- Encrypt a test plaintext using `EncryptionService`, verify we get a valid `EncryptedBlob`, and successfully decrypt it.
- Modify the base64 ciphertext/nonce of the blob and assert it raises an `EncryptionError` on decryption.
- Test `mask_key` with various lengths to ensure key components are hidden correctly.
- Test `constant_time_equals` matches correctly and resists basic timing checks.

### C. Database Lifecycle Tests (`test_database.py`)
Validate session lifecycles:
- Verify `init_engine()` initializes global sessionmakers.
- Using a test database or mock session, verify `session_scope()` commits on normal exit and rolls back on raised exceptions.

### D. Exceptions Mapping Tests (`test_exceptions.py`)
Validate custom exceptions:
- Instantiating custom subclasses of `AppError` and verifying their `status_code` maps correctly to standard HTTP status codes.

## 4. Verification Plan
Run `pytest` to execute all tests under `tests/unit/` and check code coverage.
```bash
.venv\Scripts\pytest -v
```
Ensure all tests pass.
