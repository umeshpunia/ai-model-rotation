import time
from datetime import datetime, timezone, timedelta
from typing import AsyncGenerator
from sqlalchemy.orm import Session

from app.domain.entities.api_key import ApiKey
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
            cost=cost
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
