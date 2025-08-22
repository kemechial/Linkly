"""
Performance tests using Locust for load testing
"""
from locust import HttpUser, task, between
import random
import string
import json


class LinklyUser(HttpUser):
    """Simulate user behavior for performance testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Setup user session"""
        self.signup_and_login()
    
    def signup_and_login(self):
        """Create user account and login"""
        # Generate unique email
        username = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.email = f"test_{username}@example.com"
        self.password = "TestPassword123"
        
        # Signup
        signup_response = self.client.post("/auth/signup", json={
            "email": self.email,
            "password": self.password
        })
        
        if signup_response.status_code == 200:
            # Login
            login_response = self.client.post("/auth/token", data={
                "username": self.email,
                "password": self.password
            })
            
            if login_response.status_code == 200:
                self.token = login_response.json()["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                self.created_links = []
    
    @task(3)
    def create_link(self):
        """Create a new short link"""
        if hasattr(self, 'headers'):
            target_url = f"https://example.com/{random.randint(1000, 9999)}"
            
            response = self.client.post("/links/", 
                json={"target_url": target_url},
                headers=self.headers
            )
            
            if response.status_code == 201:
                link_data = response.json()
                self.created_links.append(link_data["short_key"])
    
    @task(5)
    def use_link(self):
        """Use a created link (redirect)"""
        if hasattr(self, 'created_links') and self.created_links:
            short_key = random.choice(self.created_links)
            self.client.get(f"/{short_key}", allow_redirects=False)
    
    @task(2)
    def view_my_links(self):
        """View user's links"""
        if hasattr(self, 'headers'):
            self.client.get("/links/me", headers=self.headers)
    
    @task(1)
    def view_link_stats(self):
        """View link statistics"""
        if hasattr(self, 'created_links') and self.created_links:
            short_key = random.choice(self.created_links)
            self.client.get(f"/links/{short_key}/stats")
    
    @task(1)
    def view_user_profile(self):
        """View user profile"""
        if hasattr(self, 'headers'):
            self.client.get("/auth/me", headers=self.headers)


class AnonymousUser(HttpUser):
    """Simulate anonymous user behavior"""
    
    wait_time = between(2, 5)
    
    def on_start(self):
        """Setup anonymous session"""
        # Get some existing links to test (created by other users)
        self.test_links = [
            "testlink1", "testlink2", "testlink3"  # These would be real links in practice
        ]
    
    @task(10)
    def use_random_link(self):
        """Use random short links"""
        # In practice, these would be real short keys
        # For testing, we'll simulate with known patterns
        short_key = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.client.get(f"/{short_key}", allow_redirects=False)
    
    @task(2)
    def view_link_stats(self):
        """View link statistics as anonymous user"""
        short_key = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        self.client.get(f"/links/{short_key}/stats")


class HighVolumeUser(HttpUser):
    """Simulate high-volume user for stress testing"""
    
    wait_time = between(0.1, 0.5)  # Very frequent requests
    
    def on_start(self):
        """Setup high-volume user"""
        self.signup_and_login()
        self.create_initial_links()
    
    def signup_and_login(self):
        """Create account and login"""
        username = ''.join(random.choices(string.ascii_lowercase, k=12))
        self.email = f"hvuser_{username}@example.com"
        self.password = "HighVolumePassword123"
        
        # Signup
        self.client.post("/auth/signup", json={
            "email": self.email,
            "password": self.password
        })
        
        # Login
        login_response = self.client.post("/auth/token", data={
            "username": self.email,
            "password": self.password
        })
        
        if login_response.status_code == 200:
            self.token = login_response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.created_links = []
    
    def create_initial_links(self):
        """Create initial set of links for testing"""
        if hasattr(self, 'headers'):
            for i in range(10):
                target_url = f"https://example.com/hv_{i}_{random.randint(1000, 9999)}"
                response = self.client.post("/links/",
                    json={"target_url": target_url},
                    headers=self.headers
                )
                if response.status_code == 201:
                    self.created_links.append(response.json()["short_key"])
    
    @task(20)
    def rapid_link_usage(self):
        """Rapidly use existing links"""
        if hasattr(self, 'created_links') and self.created_links:
            short_key = random.choice(self.created_links)
            self.client.get(f"/{short_key}", allow_redirects=False)
    
    @task(5)
    def batch_create_links(self):
        """Create multiple links in quick succession"""
        if hasattr(self, 'headers'):
            for _ in range(3):
                target_url = f"https://example.com/batch_{random.randint(10000, 99999)}"
                self.client.post("/links/",
                    json={"target_url": target_url},
                    headers=self.headers
                )


# Performance test scenarios
class LoadTestScenario(HttpUser):
    """Balanced load test scenario"""
    
    tasks = [LinklyUser, AnonymousUser]
    weight = 3


class StressTestScenario(HttpUser):
    """Stress test scenario with high volume users"""
    
    tasks = [HighVolumeUser]
    weight = 1
