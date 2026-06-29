"""Security primitives: AES-GCM encryption for API keys at rest + JWT auth."""
from __future__ import annotations
import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError, EncryptionError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
# Password hashing (admin users)
# ============================================================
def hash_password(plain: str) -> str:
    """Hash a user password using bcrypt."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return _pwd_context.verify(plain, hashed)
    except Exception:
        return False


# ============================================================
# AES-GCM API key encryption (at rest)
# ============================================================
def _derive_key(secret: str, salt: str) -> bytes:
    """Derive a 32-byte AES-GCM key from secret + salt using SHA-256."""
    h = hashlib.sha256()
    h.update(salt.encode("utf-8"))
    h.update(b"|")
    h.update(secret.encode("utf-8"))
    h.update(b"|ai-gateway-pro")
    return h.digest()  # 32 bytes -> AES-256


@dataclass
class EncryptedBlob:
    """Encrypted opaque blob; nonce + ciphertext are base64."""
    nonce_b64: str
    ciphertext_b64: str

    def to_dict(self) -> dict[str, str]:
        return {"nonce": self.nonce_b64, "ciphertext": self.ciphertext_b64}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "EncryptedBlob":
        return cls(
            nonce_b64=data["nonce"],
            ciphertext_b64=data["ciphertext"],
        )


class EncryptionService:
    """AES-256-GCM at-rest encryption for API keys and secrets."""

    def __init__(self, secret: str | None = None, salt: str | None = None) -> None:
        settings = get_settings().security
        self._secret = secret or settings.secret_key
        self._salt = salt or settings.master_password_salt
        self._key = _derive_key(self._secret, self._salt)
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plaintext: str, *, associated_data: bytes | None = None) -> EncryptedBlob:
        """Encrypt a string using AES-GCM and return nonce + ciphertext."""
        if plaintext is None:
            raise EncryptionError("Cannot encrypt None value.")
        try:
            nonce = secrets.token_bytes(12)  # 96-bit nonce for GCM
            ct = self._aesgcm.encrypt(
                nonce,
                plaintext.encode("utf-8"),
                associated_data,
            )
            return EncryptedBlob(
                nonce_b64=base64.b64encode(nonce).decode("ascii"),
                ciphertext_b64=base64.b64encode(ct).decode("ascii"),
            )
        except Exception as exc:  # pragma: no cover - Crypto-level error
            raise EncryptionError(f"Encryption failed: {exc}") from exc

    def decrypt(self, blob: EncryptedBlob, *, associated_data: bytes | None = None) -> str:
        """Decrypt a previously encrypted blob back to plaintext."""
        try:
            nonce = base64.b64decode(blob.nonce_b64)
            ct = base64.b64decode(blob.ciphertext_b64)
            pt = self._aesgcm.decrypt(nonce, ct, associated_data)
            return pt.decode("utf-8")
        except Exception as exc:
            raise EncryptionError(f"Decryption failed: {exc}") from exc

    @staticmethod
    def mask_key(value: str, *, visible: int = 4) -> str:
        """Return a masked representation of a secret value for display/logging."""
        if not value:
            return ""
        if len(value) <= visible * 2:
            return "*" * len(value)
        return f"{value[:visible]}{'*' * 8}{value[-visible:]}"

    @staticmethod
    def random_key(length: int = 32) -> str:
        """Generate a random URL-safe key of `length` bytes."""
        return secrets.token_urlsafe(length)


# ============================================================
# JWT helpers
# ============================================================
class JWTService:
    """Encapsulates JWT issuance and validation."""

    def __init__(self) -> None:
        s = get_settings().security
        self._secret = s.secret_key
        self._algorithm = s.jwt_algorithm
        self._access_minutes = s.jwt_access_token_expire_minutes
        self._refresh_minutes = s.jwt_refresh_token_expire_minutes

    def _encode(self, payload: dict[str, Any], expires_minutes: int) -> str:
        now = datetime.now(tz=timezone.utc)
        payload = {
            **payload,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def issue_access_token(self, subject: str, *, role: str, extra: dict[str, Any] | None = None) -> str:
        payload: dict[str, Any] = {"sub": subject, "role": role, "type": "access"}
        if extra:
            payload.update(extra)
        return self._encode(payload, self._access_minutes)

    def issue_refresh_token(self, subject: str, *, role: str) -> str:
        return self._encode({"sub": subject, "role": role, "type": "refresh"}, self._refresh_minutes)

    def decode(self, token: str, *, expected_type: str = "access") -> dict[str, Any]:
        """Decode and validate a token; raise AuthenticationError on failure."""
        try:
            data = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except JWTError as exc:
            raise AuthenticationError(f"Invalid token: {exc}") from exc
        if expected_type and data.get("type") != expected_type:
            raise AuthenticationError(
                f"Wrong token type, expected {expected_type!r}, got {data.get('type')!r}"
            )
        return data


def constant_time_equals(a: str, b: str) -> bool:
    """Constant-time string comparison."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def generate_secret_key() -> str:
    """Generate a cryptographically strong 64-byte SECRET_KEY."""
    return secrets.token_urlsafe(64)