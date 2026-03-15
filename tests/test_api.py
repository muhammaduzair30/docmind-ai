import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.v1.routes.auth import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from unittest.mock import patch

# Use an in-memory SQLite database for testing API endpoints
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Clean up db before each test
@pytest.fixture(autouse=True)
def run_around_tests():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to DocMind AI"}


def test_unauthenticated_upload():
    response = client.post("/api/v1/upload/")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_unauthenticated_query():
    response = client.post("/api/v1/query/", json={"question": "test?"})
    assert response.status_code == 401


def test_user_registration():
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_invalid_query_validation():
    # Register and login to get token
    client.post("/api/v1/auth/register", json={"username": "q_user", "email": "q@test.com", "password": "pwd"})
    login_resp = client.post("/api/v1/auth/login", json={"username": "q_user", "password": "pwd"})
    token = login_resp.json()["access_token"]
    
    # Test short query validation (<3 chars)
    response = client.post(
        "/api/v1/query/", 
        headers={"Authorization": f"Bearer {token}"},
        json={"question": "hi"}
    )
    assert response.status_code == 422 # Pydantic validation error

def test_document_management():
    # Setup user
    client.post("/api/v1/auth/register", json={"username": "docuser", "email": "d@test.com", "password": "pwd"})
    token = client.post("/api/v1/auth/login", json={"username": "docuser", "password": "pwd"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Fetch empty list
    resp1 = client.get("/api/v1/documents/", headers=headers)
    assert resp1.status_code == 200
    assert len(resp1.json()) == 0
    
    # Delete non-existent doc
    resp2 = client.delete("/api/v1/documents/999", headers=headers)
    assert resp2.status_code == 404
