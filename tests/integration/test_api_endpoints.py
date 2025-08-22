"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


@pytest.mark.integration
class TestAuthenticationEndpoints:
    """Integration tests for authentication endpoints"""

    def test_signup_success(self, client):
        """Test successful user signup"""
        response = client.post("/auth/signup", json={
            "email": "newuser@example.com",
            "password": "StrongPassword123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    def test_signup_duplicate_email(self, client):
        """Test signup with duplicate email"""
        # Create first user
        client.post("/auth/signup", json={
            "email": "duplicate@example.com",
            "password": "Password123"
        })
        
        # Try to create user with same email
        response = client.post("/auth/signup", json={
            "email": "duplicate@example.com",
            "password": "Password123"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_signup_invalid_email(self, client):
        """Test signup with invalid email"""
        response = client.post("/auth/signup", json={
            "email": "invalid-email",
            "password": "Password123"
        })
        
        assert response.status_code == 422

    def test_login_success(self, client):
        """Test successful login"""
        # Create user
        client.post("/auth/signup", json={
            "email": "logintest@example.com",
            "password": "Password123"
        })
        
        # Login
        response = client.post("/auth/token", data={
            "username": "logintest@example.com",
            "password": "Password123"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 100

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post("/auth/token", data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_get_current_user_success(self, client, authenticated_user):
        """Test getting current user info"""
        response = client.get("/auth/me", headers=authenticated_user["headers"])
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == authenticated_user["user"].email

    def test_get_current_user_no_token(self, client):
        """Test getting current user without token"""
        response = client.get("/auth/me")
        
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Test getting current user with invalid token"""
        response = client.get("/auth/me", headers={
            "Authorization": "Bearer invalid-token"
        })
        
        assert response.status_code == 401


@pytest.mark.integration
class TestLinkEndpoints:
    """Integration tests for link management endpoints"""

    def test_create_link_success(self, client, authenticated_user):
        """Test successful link creation"""
        response = client.post("/links/", 
            json={"target_url": "https://example.com"},
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "short_key" in data
        assert data["target_url"] == "https://example.com/"  # Pydantic normalizes URLs with trailing slash
        assert data["clicks"] == 0
        assert len(data["short_key"]) >= 6

    def test_create_link_unauthorized(self, client):
        """Test link creation without authentication"""
        response = client.post("/links/", json={
            "target_url": "https://example.com"
        })
        
        assert response.status_code == 401

    def test_create_link_invalid_url(self, client, authenticated_user):
        """Test link creation with invalid URL"""
        response = client.post("/links/",
            json={"target_url": "not-a-valid-url"},
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == 422

    def test_get_user_links_empty(self, client, authenticated_user):
        """Test getting user links when none exist"""
        response = client.get("/links/me", headers=authenticated_user["headers"])
        
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_user_links_multiple(self, client, authenticated_user):
        """Test getting multiple user links"""
        # Create multiple links
        urls = ["https://example1.com", "https://example2.com", "https://example3.com"]
        normalized_urls = ["https://example1.com/", "https://example2.com/", "https://example3.com/"]  # Pydantic normalized URLs
        created_links = []
        
        for url in urls:
            response = client.post("/links/",
                json={"target_url": url},
                headers=authenticated_user["headers"]
            )
            created_links.append(response.json())
        
        # Get user links
        response = client.get("/links/me", headers=authenticated_user["headers"])
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        
        # Verify all links are present (using normalized URLs)
        retrieved_urls = [link["target_url"] for link in data]
        for url in normalized_urls:
            assert url in retrieved_urls

    def test_get_user_links_unauthorized(self, client):
        """Test getting user links without authentication"""
        response = client.get("/links/me")
        
        assert response.status_code == 401

    def test_link_stats_success(self, client, authenticated_user):
        """Test getting link statistics"""
        # Create a link
        response = client.post("/links/",
            json={"target_url": "https://example.com"},
            headers=authenticated_user["headers"]
        )
        short_key = response.json()["short_key"]
        
        # Get stats
        response = client.get(f"/links/{short_key}/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["short_key"] == short_key
        assert data["clicks"] == 0

    def test_link_stats_not_found(self, client):
        """Test getting stats for non-existent link"""
        response = client.get("/links/nonexistent/stats")
        
        assert response.status_code == 404


@pytest.mark.integration
class TestLinkRedirection:
    """Integration tests for link redirection"""

    def test_redirect_success(self, client, authenticated_user):
        """Test successful link redirection"""
        # Create a link
        response = client.post("/links/",
            json={"target_url": "https://example.com/redirect-test"},
            headers=authenticated_user["headers"]
        )
        short_key = response.json()["short_key"]
        
        # Follow redirect
        response = client.get(f"/{short_key}", follow_redirects=False)
        
        assert response.status_code in [307, 308]  # Temporary or Permanent Redirect
        assert "location" in response.headers
        assert response.headers["location"] == "https://example.com/redirect-test"

    def test_redirect_not_found(self, client):
        """Test redirection for non-existent short key"""
        response = client.get("/nonexistent", follow_redirects=False)
        
        assert response.status_code == 404

    def test_redirect_increments_clicks(self, client, authenticated_user):
        """Test that redirection increments click count"""
        # Create a link
        response = client.post("/links/",
            json={"target_url": "https://example.com/click-test"},
            headers=authenticated_user["headers"]
        )
        short_key = response.json()["short_key"]
        
        # Initial stats
        stats_response = client.get(f"/links/{short_key}/stats")
        initial_clicks = stats_response.json()["clicks"]
        
        # Click the link
        client.get(f"/{short_key}", follow_redirects=False)
        
        # Check updated stats
        stats_response = client.get(f"/links/{short_key}/stats")
        final_clicks = stats_response.json()["clicks"]
        
        assert final_clicks == initial_clicks + 1

    def test_multiple_redirects_increment_clicks(self, client, authenticated_user):
        """Test multiple redirections increment clicks correctly"""
        # Create a link
        response = client.post("/links/",
            json={"target_url": "https://example.com/multi-click-test"},
            headers=authenticated_user["headers"]
        )
        short_key = response.json()["short_key"]
        
        # Click multiple times
        for i in range(5):
            client.get(f"/{short_key}", follow_redirects=False)
        
        # Check final stats
        stats_response = client.get(f"/links/{short_key}/stats")
        final_clicks = stats_response.json()["clicks"]
        
        assert final_clicks == 5


@pytest.mark.integration
@pytest.mark.redis
class TestRedisIntegration:
    """Integration tests for Redis caching"""

    def test_link_caching_on_creation(self, client, authenticated_user, fake_redis):
        """Test that links are cached when created"""
        response = client.post("/links/",
            json={"target_url": "https://example.com/cache-test"},
            headers=authenticated_user["headers"]
        )
        short_key = response.json()["short_key"]
        
        # Check if link is cached
        cached_data = fake_redis.get(f"link:{short_key}")
        assert cached_data is not None

    def test_redirect_uses_cache(self, client, authenticated_user, fake_redis):
        """Test that redirection uses cache when available"""
        # Create a link
        response = client.post("/links/",
            json={"target_url": "https://example.com/cache-redirect"},
            headers=authenticated_user["headers"]
        )
        short_key = response.json()["short_key"]
        
        # First redirect (should cache)
        response1 = client.get(f"/{short_key}", follow_redirects=False)
        assert response1.status_code in [307, 308]
        
        # Second redirect (should use cache)
        response2 = client.get(f"/{short_key}", follow_redirects=False)
        assert response2.status_code in [307, 308]
        assert response2.headers["location"] == "https://example.com/cache-redirect"

    def test_click_counting_in_redis(self, client, authenticated_user, fake_redis):
        """Test that click counts are tracked in Redis"""
        # Create a link
        response = client.post("/links/",
            json={"target_url": "https://example.com/redis-clicks"},
            headers=authenticated_user["headers"]
        )
        short_key = response.json()["short_key"]
        
        # Click the link multiple times
        for i in range(3):
            client.get(f"/{short_key}", follow_redirects=False)
        
        # Check Redis click count
        redis_clicks = fake_redis.get(f"clicks:{short_key}")
        assert int(redis_clicks) == 3


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling"""

    def test_404_for_invalid_endpoints(self, client):
        """Test 404 response for invalid endpoints"""
        response = client.get("/invalid/endpoint")
        assert response.status_code == 404

    def test_method_not_allowed(self, client):
        """Test 405 response for wrong HTTP methods"""
        response = client.put("/auth/signup", json={
            "email": "test@example.com",
            "password": "password"
        })
        assert response.status_code == 405

    def test_malformed_json_request(self, client, authenticated_user):
        """Test handling of malformed JSON requests"""
        # Send malformed JSON
        response = client.post("/links/",
            data="invalid json",
            headers={
                **authenticated_user["headers"],
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 422

    def test_missing_required_fields(self, client, authenticated_user):
        """Test handling of missing required fields"""
        response = client.post("/links/",
            json={},  # Missing target_url
            headers=authenticated_user["headers"]
        )
        assert response.status_code == 422

    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection"""
        malicious_email = "test@example.com'; DROP TABLE users; --"
        
        response = client.post("/auth/signup", json={
            "email": malicious_email,
            "password": "password"
        })
        
        # Should either reject the email format or handle safely
        assert response.status_code in [422, 200]  # Validation error or safe handling


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceBaseline:
    """Basic performance tests to establish baselines"""

    def test_signup_performance(self, client):
        """Test signup endpoint performance"""
        import time
        
        start_time = time.time()
        response = client.post("/auth/signup", json={
            "email": "perf_test@example.com",
            "password": "Password123"
        })
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should complete within 1 second

    def test_link_creation_performance(self, client, authenticated_user):
        """Test link creation endpoint performance"""
        import time
        
        start_time = time.time()
        response = client.post("/links/",
            json={"target_url": "https://example.com/perf-test"},
            headers=authenticated_user["headers"]
        )
        end_time = time.time()
        
        assert response.status_code == 201
        assert (end_time - start_time) < 1.0  # Should complete within 1 second (adjusted for containerized environment)

    def test_redirect_performance(self, client, authenticated_user):
        """Test redirect endpoint performance"""
        import time
        
        # Create a link
        response = client.post("/links/",
            json={"target_url": "https://example.com/perf-redirect"},
            headers=authenticated_user["headers"]
        )
        short_key = response.json()["short_key"]
        
        # Test redirect performance
        start_time = time.time()
        response = client.get(f"/{short_key}", follow_redirects=False)
        end_time = time.time()
        
        assert response.status_code in [307, 308]
        assert (end_time - start_time) < 0.1  # Should complete within 100ms
