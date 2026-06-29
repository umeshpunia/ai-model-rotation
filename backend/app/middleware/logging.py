import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

_logger = get_logger("http")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        
        # Inject client IP
        client_ip = request.client.host if request.client else "unknown"
        
        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            
            _logger.info(
                "http.request",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=client_ip
            )
            return response
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            _logger.error(
                "http.request.failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=duration_ms,
                client_ip=client_ip
            )
            raise e
