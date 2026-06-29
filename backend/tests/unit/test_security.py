import pytest
from app.core.security import (
    hash_password,
    verify_password,
    EncryptionService,
    constant_time_equals,
    generate_secret_key,
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
