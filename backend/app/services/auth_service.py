from typing import Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.database import get_db
from app.core.security import verify_password, JWTService
from app.core.exceptions import AuthenticationError
from app.domain.entities.user import User
from app.domain.enums import UserRole
from app.repositories.user_repository import UserRepository

# OAuth2 schema for extracting bearer token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

class AuthService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.jwt_service = JWTService()

    def authenticate_user(self, username: str, plain_password: str) -> User:
        """Authenticate username against stored hashed password."""
        user = self.user_repo.get_by_username(username)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid username or password.")
            
        if not verify_password(plain_password, user.hashed_password):
            raise AuthenticationError("Invalid username or password.")
            
        return user

    def create_tokens(self, user: User) -> dict[str, str]:
        """Issue access and refresh tokens for a user."""
        access_token = self.jwt_service.issue_access_token(
            subject=user.username,
            role=user.role.value
        )
        refresh_token = self.jwt_service.issue_refresh_token(
            subject=user.username,
            role=user.role.value
        )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_access_token(self, refresh_token: str) -> dict[str, str]:
        """Verify refresh token and issue new access/refresh tokens."""
        try:
            payload = self.jwt_service.decode(refresh_token, expected_type="refresh")
            username = payload.get("sub")
            if not username:
                raise AuthenticationError("Invalid refresh token payload.")
                
            user = self.user_repo.get_by_username(username)
            if not user or not user.is_active:
                raise AuthenticationError("User is inactive or deleted.")
                
            return self.create_tokens(user)
        except AuthenticationError as e:
            raise e
        except Exception as e:
            raise AuthenticationError(f"Token refresh failed: {str(e)}")

# Dependency injection helpers
def get_auth_service(session: Session = Depends(get_db)) -> AuthService:
    return AuthService(session)

async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    session: Session = Depends(get_db)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    try:
        jwt_service = JWTService()
        payload = jwt_service.decode(token, expected_type="access")
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        user_repo = UserRepository(session)
        user = user_repo.get_by_username(username)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive or invalid user account"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )

def require_role(required_role: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if required_role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return dependency
