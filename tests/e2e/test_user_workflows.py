"""
End-to-end tests for complete user workflows
"""
import pytest
import time
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.e2e
class TestUserWorkflows:
    """Test complete user workflows from start to finish"""

    def test_complete_user_journey(self, client):
        """Test complete user journey: signup -> login -> create links -> use links"""
        # Step 1: User signs up
        signup_response = client.post("/auth/signup", json={
            "email": "journey_user@example.com",
            "password": "SecurePassword123"
        })
        assert signup_response.status_code == 200
        user_data = signup_response.json()
        assert user_data["email"] == "journey_user@example.com"
        
        # Step 2: User logs in
        login_response = client.post("/auth/token", data={
            "username": "journey_user@example.com",
            "password": "SecurePassword123"
        })
        assert login_response.status_code == 200
        token_data = login_response.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 3: User creates multiple links
        urls_to_shorten = [
            "https://docs.python.org/3/",
            "https://fastapi.tiangolo.com/",
            "https://github.com/",
            "https://stackoverflow.com/"
        ]
        
        created_links = []
        for url in urls_to_shorten:
            create_response = client.post("/links/",
                json={"target_url": url},
                headers=headers
            )
            assert create_response.status_code == 201
            link_data = create_response.json()
            created_links.append(link_data)
        
        # Step 4: Verify user can see all their links
        my_links_response = client.get("/links/me", headers=headers)
        assert my_links_response.status_code == 200
        my_links = my_links_response.json()
        assert len(my_links) == 4
        
        # Step 5: Test redirection for each link
        for i, link in enumerate(created_links):
            redirect_response = client.get(f"/{link['short_key']}", follow_redirects=False)
            assert redirect_response.status_code in [307, 308]
            assert redirect_response.headers["location"] == urls_to_shorten[i]
        
        # Step 6: Check statistics for links
        for link in created_links:
            stats_response = client.get(f"/links/{link['short_key']}/stats")
            assert stats_response.status_code == 200
            stats = stats_response.json()
            assert stats["clicks"] == 1  # Each link was clicked once

    def test_anonymous_user_workflow(self, client):
        """Test what anonymous users can and cannot do"""
        # Anonymous users should be able to:
        # 1. Access redirect links (if they have the short key)
        # 2. View link statistics (public information)
        
        # First, create a link with authenticated user for testing
        signup_response = client.post("/auth/signup", json={
            "email": "link_creator@example.com",
            "password": "Password123"
        })
        login_response = client.post("/auth/token", data={
            "username": "link_creator@example.com",
            "password": "Password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        create_response = client.post("/links/",
            json={"target_url": "https://example.com/public-link"},
            headers=headers
        )
        short_key = create_response.json()["short_key"]
        
        # Now test as anonymous user
        # Should be able to use redirect
        redirect_response = client.get(f"/{short_key}", follow_redirects=False)
        assert redirect_response.status_code in [307, 308]
        assert redirect_response.headers["location"] == "https://example.com/public-link"
        
        # Should be able to view stats
        stats_response = client.get(f"/links/{short_key}/stats")
        assert stats_response.status_code == 200
        
        # Should NOT be able to create links
        create_anon_response = client.post("/links/", json={
            "target_url": "https://example.com"
        })
        assert create_anon_response.status_code == 401
        
        # Should NOT be able to view user's private link list
        my_links_response = client.get("/links/me")
        assert my_links_response.status_code == 401

    def test_multiple_users_isolation(self, client):
        """Test that multiple users' data is properly isolated"""
        # Create two users
        users = [
            {"email": "user1@example.com", "password": "Password123"},
            {"email": "user2@example.com", "password": "Password123"}
        ]
        
        user_tokens = []
        user_links = []
        
        for user in users:
            # Signup
            signup_response = client.post("/auth/signup", json=user)
            assert signup_response.status_code == 200
            
            # Login
            login_response = client.post("/auth/token", data={
                "username": user["email"],
                "password": user["password"]
            })
            token = login_response.json()["access_token"]
            user_tokens.append(token)
            
            # Create links for each user
            headers = {"Authorization": f"Bearer {token}"}
            links = []
            for i in range(3):
                create_response = client.post("/links/",
                    json={"target_url": f"https://example.com/{user['email']}/{i}"},
                    headers=headers
                )
                links.append(create_response.json())
            user_links.append(links)
        
        # Verify isolation: each user should only see their own links
        for i, token in enumerate(user_tokens):
            headers = {"Authorization": f"Bearer {token}"}
            my_links_response = client.get("/links/me", headers=headers)
            my_links = my_links_response.json()
            
            assert len(my_links) == 3
            for link in my_links:
                assert users[i]["email"] in link["target_url"]

    def test_link_sharing_workflow(self, client):
        """Test workflow of sharing links between users"""
        # User A creates a link
        signup_a = client.post("/auth/signup", json={
            "email": "user_a@example.com",
            "password": "Password123"
        })
        login_a = client.post("/auth/token", data={
            "username": "user_a@example.com",
            "password": "Password123"
        })
        token_a = login_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        
        create_response = client.post("/links/",
            json={"target_url": "https://example.com/shared-content"},
            headers=headers_a
        )
        shared_link = create_response.json()
        short_key = shared_link["short_key"]
        
        # User B signs up but doesn't create the link
        signup_b = client.post("/auth/signup", json={
            "email": "user_b@example.com",
            "password": "Password123"
        })
        
        # User B can still use the shared link (anonymous access)
        redirect_response = client.get(f"/{short_key}", follow_redirects=False)
        assert redirect_response.status_code in [307, 308]
        assert redirect_response.headers["location"] == "https://example.com/shared-content"
        
        # Both users can view stats
        stats_response = client.get(f"/links/{short_key}/stats")
        assert stats_response.status_code == 200
        assert stats_response.json()["clicks"] == 1

    def test_high_frequency_usage_workflow(self, client):
        """Test workflow with high frequency link usage"""
        # Create user and link
        client.post("/auth/signup", json={
            "email": "heavy_user@example.com",
            "password": "Password123"
        })
        login_response = client.post("/auth/token", data={
            "username": "heavy_user@example.com",
            "password": "Password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        create_response = client.post("/links/",
            json={"target_url": "https://example.com/popular-content"},
            headers=headers
        )
        short_key = create_response.json()["short_key"]
        
        # Simulate high frequency usage
        click_count = 50
        for i in range(click_count):
            redirect_response = client.get(f"/{short_key}", follow_redirects=False)
            assert redirect_response.status_code in [307, 308]
        
        # Verify click count is accurate
        stats_response = client.get(f"/links/{short_key}/stats")
        stats = stats_response.json()
        assert stats["clicks"] == click_count

    def test_concurrent_user_workflow(self, client):
        """Test workflow with concurrent user actions"""
        import threading
        import time
        
        # Create a shared link first
        client.post("/auth/signup", json={
            "email": "concurrent_test@example.com",
            "password": "Password123"
        })
        login_response = client.post("/auth/token", data={
            "username": "concurrent_test@example.com",
            "password": "Password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        create_response = client.post("/links/",
            json={"target_url": "https://example.com/concurrent-test"},
            headers=headers
        )
        short_key = create_response.json()["short_key"]
        
        # Define concurrent click function
        results = []
        
        def click_link():
            try:
                response = client.get(f"/{short_key}", follow_redirects=False)
                results.append(response.status_code)
            except Exception as e:
                results.append(f"Error: {e}")
        
        # Start multiple threads to click simultaneously
        threads = []
        thread_count = 10
        
        for i in range(thread_count):
            thread = threading.Thread(target=click_link)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded
        assert len(results) == thread_count
        for result in results:
            assert result in [307, 308], f"Unexpected result: {result}"
        
        # Verify final click count
        time.sleep(1)  # Give time for Redis updates
        stats_response = client.get(f"/links/{short_key}/stats")
        stats = stats_response.json()
        assert stats["clicks"] == thread_count


@pytest.mark.e2e
@pytest.mark.slow
class TestSystemReliability:
    """Test system reliability and edge cases"""

    def test_system_handles_invalid_data_gracefully(self, client):
        """Test system handles various invalid inputs gracefully"""
        # Test with very long URLs
        very_long_url = "https://example.com/" + "x" * 10000
        
        client.post("/auth/signup", json={
            "email": "edge_case_user@example.com",
            "password": "Password123"
        })
        login_response = client.post("/auth/token", data={
            "username": "edge_case_user@example.com",
            "password": "Password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Should handle gracefully (either accept or reject predictably)
        response = client.post("/links/",
            json={"target_url": very_long_url},
            headers=headers
        )
        assert response.status_code in [201, 400, 422]  # Accept or predictable rejection
        
        # Test with special characters in URL
        special_url = "https://example.com/測試?param=value&other=測試"
        response = client.post("/links/",
            json={"target_url": special_url},
            headers=headers
        )
        assert response.status_code in [201, 400, 422]

    def test_system_performance_under_load(self, client):
        """Test basic system performance under simulated load"""
        # Create multiple users and links rapidly
        import time
        
        start_time = time.time()
        
        for i in range(10):
            # Create user
            signup_response = client.post("/auth/signup", json={
                "email": f"load_user_{i}@example.com",
                "password": "Password123"
            })
            assert signup_response.status_code == 200
            
            # Login
            login_response = client.post("/auth/token", data={
                "username": f"load_user_{i}@example.com",
                "password": "Password123"
            })
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Create multiple links
            for j in range(5):
                create_response = client.post("/links/",
                    json={"target_url": f"https://example.com/load_test_{i}_{j}"},
                    headers=headers
                )
                assert create_response.status_code == 201
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within reasonable time (adjust based on requirements)
        assert total_time < 30, f"Load test took {total_time:.2f} seconds"

    def test_database_consistency_after_operations(self, client):
        """Test database remains consistent after various operations"""
        # Create user and perform various operations
        client.post("/auth/signup", json={
            "email": "consistency_user@example.com",
            "password": "Password123"
        })
        login_response = client.post("/auth/token", data={
            "username": "consistency_user@example.com",
            "password": "Password123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create links
        created_links = []
        for i in range(5):
            response = client.post("/links/",
                json={"target_url": f"https://example.com/consistency_{i}"},
                headers=headers
            )
            created_links.append(response.json())
        
        # Use links multiple times
        for link in created_links:
            for _ in range(3):
                client.get(f"/{link['short_key']}", follow_redirects=False)
        
        # Verify data consistency
        my_links_response = client.get("/links/me", headers=headers)
        my_links = my_links_response.json()
        assert len(my_links) == 5
        
        # Verify each link's click count
        for link in created_links:
            stats_response = client.get(f"/links/{link['short_key']}/stats")
            stats = stats_response.json()
            assert stats["clicks"] == 3

    def test_error_recovery_workflow(self, client):
        """Test system recovery from various error conditions"""
        # Test recovery from authentication errors
        # Invalid login followed by correct login
        
        # First, create a user
        client.post("/auth/signup", json={
            "email": "recovery_user@example.com",
            "password": "CorrectPassword123"
        })
        
        # Try invalid login
        invalid_response = client.post("/auth/token", data={
            "username": "recovery_user@example.com",
            "password": "WrongPassword"
        })
        assert invalid_response.status_code == 401
        
        # Then correct login should work
        valid_response = client.post("/auth/token", data={
            "username": "recovery_user@example.com",
            "password": "CorrectPassword123"
        })
        assert valid_response.status_code == 200
        
        # System should work normally after recovery
        token = valid_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        create_response = client.post("/links/",
            json={"target_url": "https://example.com/recovery-test"},
            headers=headers
        )
        assert create_response.status_code == 201
