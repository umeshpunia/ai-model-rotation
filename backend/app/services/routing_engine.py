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
            usable_triplets.sort(key=lambda x: (x[0].priority, x[1].priority))
            
        elif mode == RoutingMode.ROUND_ROBIN:
            usable_triplets.sort(key=lambda x: (x[1].last_used_at is not None, x[1].last_used_at))
            
        elif mode == RoutingMode.LEAST_USED:
            usable_triplets.sort(key=lambda x: x[1].usage_count)
            
        elif mode == RoutingMode.FASTEST:
            usable_triplets.sort(key=lambda x: (x[1].avg_latency_ms is not None, x[1].avg_latency_ms))
            
        elif mode == RoutingMode.LOWEST_COST:
            usable_triplets.sort(key=lambda x: (x[2].input_cost_per_1k + x[2].output_cost_per_1k))
            
        elif mode == RoutingMode.HIGHEST_SUCCESS:
            usable_triplets.sort(key=lambda x: x[1].success_count / (x[1].usage_count + 1), reverse=True)
            
        elif mode == RoutingMode.RANDOM:
            random.shuffle(usable_triplets)
            
        elif mode == RoutingMode.AI_OPTIMIZED:
            if task_type:
                usable_triplets.sort(key=lambda x: task_type in x[2].task_types, reverse=True)
            else:
                usable_triplets.sort(key=lambda x: (x[0].priority, x[1].priority))
                
        return usable_triplets
