import time
from typing import Dict, List
from fastapi import Request, HTTPException, status
from app.core.config import get_settings

class RateLimiter:
    def __init__(self, requests_limit: int = 100, window_seconds: int = 60) -> None:
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        # In-memory store: {client_ip: [timestamps]}
        self.history: Dict[str, List[float]] = {}

    def is_rate_limited(self, client_ip: str) -> bool:
        now = time.time()
        
        # Initialize history
        if client_ip not in self.history:
            self.history[client_ip] = []
            
        timestamps = self.history[client_ip]
        
        # Prune expired timestamps
        cutoff = now - self.window_seconds
        self.history[client_ip] = [t for t in timestamps if t > cutoff]
        
        # Check limit
        if len(self.history[client_ip]) >= self.requests_limit:
            return True
            
        self.history[client_ip].append(now)
        return False

# Global instance with default 100 requests per minute
_global_limiter = RateLimiter(requests_limit=100, window_seconds=60)

def check_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if _global_limiter.is_rate_limited(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
