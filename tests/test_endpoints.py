import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def signup_user():
    # Always try to sign up, ignore if already exists
    client.post("/auth/signup", json={"email": "testuser@example.com", "password": "testpass123"})

def get_token():
    signup_user()
    response = client.post("/auth/token", data={"username": "testuser@example.com", "password": "testpass123"})
    assert response.status_code == 200
    return response.json()["access_token"]

def test_signup():
    response = client.post("/auth/signup", json={"email": "testuser@example.com", "password": "testpass123"})
    assert response.status_code in (200, 400)


def test_login():
    signup_user()
    response = client.post("/auth/token", data={"username": "testuser@example.com", "password": "testpass123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_get_me():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"


def test_create_link():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/links/", json={"target_url": "https://example.com"}, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "short_key" in data
    # Accept trailing slash in normalized URL
    assert data["target_url"].rstrip("/") == "https://example.com"


def test_my_links():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/links/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_link_stats():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    # Create a link first
    response = client.post("/links/", json={"target_url": "https://example.com"}, headers=headers)
    assert response.status_code == 201
    short_key = response.json()["short_key"]
    # Now get stats
    response = client.get(f"/links/{short_key}/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["short_key"] == short_key
    assert "clicks" in data
