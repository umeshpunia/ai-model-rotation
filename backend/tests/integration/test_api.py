import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel

from app.main import app
from app.core.database import session_scope, get_settings, dispose_engine
from app.domain.entities.user import User
from app.core.security import hash_password
from app.domain.enums import UserRole

import os

@pytest.fixture(name="client", scope="function")
def client_fixture():
    # Use isolated local SQLite database file for thread-safe API tests
    settings = get_settings()
    original_url = settings.database.database_test_url
    db_file = "test_api.db"
    settings.database.database_test_url = f"sqlite:///{db_file}"
    dispose_engine()
    
    from app.core.database import get_engine
    SQLModel.metadata.create_all(get_engine())
    
    # Run database admin seed
    with session_scope() as session:
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
        
    client = TestClient(app)
    yield client
    
    SQLModel.metadata.drop_all(get_engine())
    settings.database.database_test_url = original_url
    dispose_engine()
    
    # Clean up file
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

def test_health_check_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}

def test_admin_authentication_flow(client: TestClient):
    # Test valid login
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Test invalid login
    response_fail = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrongpassword"}
    )
    assert response_fail.status_code == 401
    
    # Test refresh token
    refresh_token = data["refresh_token"]
    response_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response_refresh.status_code == 200
    assert "access_token" in response_refresh.json()

def test_protected_endpoints_require_auth(client: TestClient):
    # Test list providers without token -> 401
    response = client.get("/api/v1/providers")
    assert response.status_code == 401
    
    # Login to get token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    token = login_resp.json()["access_token"]
    
    # Try with auth token -> 200
    headers = {"Authorization": f"Bearer {token}"}
    response_auth = client.get("/api/v1/providers", headers=headers)
    assert response_auth.status_code == 200
