from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.schemas.user import LoginRequest, TokenResponse, RefreshRequest
from app.services.auth_service import AuthService, get_auth_service

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Authenticate credentials and return JWT tokens."""
    try:
        user = auth_service.authenticate_user(payload.username, payload.password)
        tokens = auth_service.create_tokens(user)
        expires_seconds = get_settings().security.jwt_access_token_expire_minutes * 60
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=expires_seconds
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Refresh an access token using a valid refresh token."""
    try:
        tokens = auth_service.refresh_access_token(payload.refresh_token)
        expires_seconds = get_settings().security.jwt_access_token_expire_minutes * 60
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=expires_seconds
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
