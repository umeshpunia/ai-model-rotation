from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import AsyncGenerator

from app.core.config import get_settings
from app.core.database import init_engine, session_scope, get_engine
from app.core.exceptions import AuthenticationError, NotFoundError, ValidationError, UpstreamError
from app.core.scheduler import get_scheduler_manager
from app.core.security import hash_password
from app.domain.entities.user import User
from app.domain.enums import UserRole
from app.middleware.logging import LoggingMiddleware
from app.routers import api_router, gateway_router
from app.core.logging import get_logger

_logger = get_logger("main")

def seed_default_user() -> None:
    """Seed the default administrator account if the users table is empty."""
    with session_scope() as session:
        try:
            # Query if any user exists
            stmt = select(User)
            existing = session.exec(stmt).first()
            if not existing:
                _logger.info("db.seeding_admin")
                admin_user = User(
                    username="admin",
                    email="[email protected]",
                    full_name="Default Administrator",
                    hashed_password=hash_password("admin123"),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_superuser=True
                )
                session.add(admin_user)
                session.commit()
                _logger.info("db.admin_seeded_successfully")
        except Exception as e:
            _logger.error("db.seeding_failed", error=str(e))

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifecycle lifespan manager."""
    _logger.info("app.lifespan.startup")
    # Initialize DB engine
    init_engine()
    
    # Seeding
    seed_default_user()
    
    # Start Scheduler
    scheduler = get_scheduler_manager()
    scheduler.start()
    
    yield
    
    _logger.info("app.lifespan.shutdown")
    # Stop Scheduler
    scheduler.shutdown()

# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title="AI Gateway Pro",
    version="1.0.0",
    description="Intelligent AI Provider Routing & Failover Gateway API Backend",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.cors_origins,
    allow_credentials=settings.cors.cors_allow_credentials,
    allow_methods=settings.cors.cors_allow_methods,
    allow_headers=settings.cors.cors_allow_headers,
)

# Tracing Request Logging Middleware
app.add_middleware(LoggingMiddleware)

# Global Exception Handlers
@app.exception_handler(AuthenticationError)
def auth_exception_handler(request: Request, exc: AuthenticationError) -> Response:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc), "error_type": "authentication_error"}
    )

@app.exception_handler(NotFoundError)
def not_found_exception_handler(request: Request, exc: NotFoundError) -> Response:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "error_type": "not_found_error"}
    )

@app.exception_handler(ValidationError)
def validation_exception_handler(request: Request, exc: ValidationError) -> Response:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_type": "validation_error"}
    )

@app.exception_handler(UpstreamError)
def upstream_exception_handler(request: Request, exc: UpstreamError) -> Response:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc), "error_type": "upstream_error"}
    )

# Register Routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(gateway_router, prefix="/v1")
