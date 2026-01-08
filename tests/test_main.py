"""Tests for main application endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test root endpoint returns API information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["app"] == "EvoTrack"
    assert data["status"] == "running"
    assert "version" in data
    assert "docs" in data


def test_health_check(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert data["app"] == "EvoTrack"


def test_api_docs_accessible(client: TestClient):
    """Test that API documentation is accessible."""
    response = client.get("/api/docs")
    assert response.status_code == 200


def test_openapi_schema(client: TestClient):
    """Test OpenAPI schema is available."""
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert schema["info"]["title"] == "EvoTrack"


@pytest.mark.parametrize("invalid_path", [
    "/nonexistent",
    "/api/v1/invalid",
    "/random/path",
])
def test_404_on_invalid_paths(client: TestClient, invalid_path: str):
    """Test that invalid paths return 404."""
    response = client.get(invalid_path)
    assert response.status_code == 404
