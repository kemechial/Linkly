#!/usr/bin/env python3
"""
Debug script to check authentication flow
"""
import os
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

# Print config values
print("=== CONFIG DEBUG ===")
print(f"SECRET_KEY: {settings.secret_key}")
print(f"ALGORITHM: {settings.algorithm}")
print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.access_token_expire_minutes}")
print("")

client = TestClient(app)

# Test signup
print("=== SIGNUP TEST ===")
signup_response = client.post("/auth/signup", json={
    "email": "debug@example.com",
    "password": "DebugPassword123"
})
print(f"Signup status: {signup_response.status_code}")
print(f"Signup response: {signup_response.json()}")
print("")

# Test login
print("=== LOGIN TEST ===")
login_response = client.post("/auth/token", data={
    "username": "debug@example.com",
    "password": "DebugPassword123"
})
print(f"Login status: {login_response.status_code}")
if login_response.status_code == 200:
    token_data = login_response.json()
    token = token_data["access_token"]
    print(f"Token: {token}")
    
    # Test protected endpoint
    print("=== PROTECTED ENDPOINT TEST ===")
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/auth/me", headers=headers)
    print(f"Auth/me status: {me_response.status_code}")
    print(f"Auth/me response: {me_response.json()}")
    
    # Test link creation
    print("=== LINK CREATION TEST ===")
    create_response = client.post("/links/", 
        json={"target_url": "https://example.com"},
        headers=headers
    )
    print(f"Link creation status: {create_response.status_code}")
    print(f"Link creation response: {create_response.json()}")
else:
    print(f"Login failed: {login_response.json()}")
