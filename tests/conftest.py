"""Pytest configuration and fixtures for testing."""

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://evotrack_test:test_password@localhost:5432/evotrack_test_db"
)

# Create test engine with StaticPool for SQLite or NullPool for PostgreSQL
engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool if "sqlite" in TEST_DATABASE_URL else None,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables before running tests."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Get a test database session.
    Creates a new session for each test and rolls back after.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Get a test client with database session override.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def test_organization_data():
    """Sample organization data for testing."""
    return {
        "name": "Test Organization",
        "slug": "test-org",
        "description": "A test organization",
    }


@pytest.fixture
def test_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "code": "TEST-001",
        "description": "A test project",
        "status": "active",
    }


# Authentication fixtures (to be implemented later)
@pytest.fixture
def auth_headers(client: TestClient, test_user_data):
    """
    Get authentication headers for authenticated requests.
    TODO: Implement after auth module is ready.
    """
    # This will be implemented when auth module is complete
    # response = client.post("/api/v1/auth/login", json={
    #     "email": test_user_data["email"],
    #     "password": test_user_data["password"]
    # })
    # token = response.json()["access_token"]
    # return {"Authorization": f"Bearer {token}"}
    return {}
