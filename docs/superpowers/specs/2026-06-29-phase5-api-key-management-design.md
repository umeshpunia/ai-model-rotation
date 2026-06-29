# Design Specification: Phase 5 API Key Management

## 1. Goal
Implement a secure, high-performance API Key CRUD Service (`ApiKeyService`) for AI Gateway Pro. Key management must encrypt credentials at rest, support dynamic testing/validation using provider plugins, mask keys in output, enforce uniqueness via cryptographic fingerprints, and track health, priority, latency, and status.

## 2. Requirements & Scope
- **Cryptographic Operations**:
  - Encrypt raw credentials using AES-256-GCM. Nonce and ciphertext are stored as a JSON-encoded string in `encrypted_key`.
  - Expose a `reveal` method that decrypts and returns plaintext credentials.
  - Generate a SHA-256 fingerprint of the plaintext API key. Deduplicate keys by provider + fingerprint to prevent redundancy.
- **CRUD Operations**:
  - Add key with automatic encryption, fingerprinting, and masking (`key_hint`).
  - Edit key (re-runs encryption/fingerprinting if the plaintext value is updated).
  - Delete key.
  - Enable/disable key.
- **Diagnostics and Health Verification**:
  - Test key (performs live upstream validation via provider plugins).
  - Update health status (`healthy`, `cooldown`, `invalid`, `expired`, `quota_reached`) and latency statistics.

## 3. Design Details

### A. API Key Service (`services/api_key_service.py`)
- **Encryption Helper**: Instantiates `app.core.security.EncryptionService`.
- **Deduplication Check**:
  ```python
  fingerprint = hashlib.sha256(raw_key.encode()).hexdigest()
  existing = self.key_repo.get_by_fingerprint(provider_id, fingerprint)
  if existing:
      raise ValidationError("This API key is already registered for this provider.")
  ```
- **CRUD Implementation**:
  - `create_key(...)`: Computes fingerprint, generates hint, encrypts payload, sets initial status to `KeyStatus.UNKNOWN`, and inserts.
  - `update_key(...)`: Updates fields, re-encrypts if key value changes.
  - `delete_key(...)`: Deletes the key record.
  - `test_key_connection(...)`: Fetches provider, decrypts key, delegates to `BaseProviderPlugin.test_connection`, records time elapsed for latency, and updates the key status.

## 4. Verification Plan
- **Unit Tests (`tests/unit/test_keys.py`)**:
  - Test creation, encryption validity, and deduplication detection.
  - Test decryption/reveal constraints.
  - Test key status transitions (healthy, disabled, cooldown).
  - Mock connection tests using mock plugins and verify key statistics are updated.
