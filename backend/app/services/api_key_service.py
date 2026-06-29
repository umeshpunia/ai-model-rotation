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
