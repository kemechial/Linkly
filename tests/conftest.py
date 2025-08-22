"""
Production-grade test configuration and fixtures
"""
import os
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient
import fakeredis
import factory
from datetime import datetime

from app.database import Base
from app.dependencies import get_db
from app.main import app
from app import models
from app.services.redis_cache import link_cache

# Test Database Configuration
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/linkly_test")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def engine():
    """Create test database engine"""
    return create_engine(TEST_DATABASE_URL, echo=False)

@pytest.fixture(scope="session")  
def tables(engine):
    """Create all database tables for testing"""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(engine):
    """Create a fresh database session for each test"""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    # Clean up all data after test but keep the tables
    session.query(models.Link).delete()
    session.query(models.User).delete() 
    session.commit()
    session.close()

@pytest.fixture
def client(db_session):
    """Create test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
async def async_client(db_session):
    """Create async test client"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture
def fake_redis():
    """Create fake Redis instance for testing"""
    fake_redis_instance = fakeredis.FakeStrictRedis(decode_responses=True)
    # Patch the Redis client in cache service
    original_redis = link_cache.redis
    link_cache.redis = fake_redis_instance
    yield fake_redis_instance
    link_cache.redis = original_redis

# Factory Classes for Test Data
class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating test users"""
    class Meta:
        model = models.User
        sqlalchemy_session_persistence = "commit"
        exclude = ('password',)  # Exclude password from model creation

    email = factory.Faker('email')
    password = "testpassword123"  # Default password, can be overridden but not passed to model
    
    @factory.lazy_attribute
    def hashed_password(self):
        from app.auth import get_password_hash
        return get_password_hash(self.password)

class LinkFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating test links"""
    class Meta:
        model = models.Link
        sqlalchemy_session_persistence = "commit"

    short_key = factory.Faker('lexify', text='????????')
    target_url = factory.Faker('url')
    clicks = 0
    owner = factory.SubFactory(UserFactory)

@pytest.fixture
def user_factory(db_session):
    """User factory with session"""
    UserFactory._meta.sqlalchemy_session = db_session
    return UserFactory

@pytest.fixture
def link_factory(db_session):
    """Link factory with session"""
    LinkFactory._meta.sqlalchemy_session = db_session
    return LinkFactory

@pytest.fixture
def test_user(db_session, user_factory):
    """Create a test user"""
    return user_factory()

@pytest.fixture
def authenticated_user(client, test_user):
    """Create authenticated user with token"""
    # Create user directly in database
    response = client.post("/auth/signup", json={
        "email": test_user.email,
        "password": "testpassword123"
    })
    
    # Get authentication token
    login_response = client.post("/auth/token", data={
        "username": test_user.email,
        "password": "testpassword123"
    })
    
    token = login_response.json()["access_token"]
    return {
        "user": test_user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }

@pytest.fixture
def test_links(db_session, link_factory, test_user):
    """Create test links"""
    links = []
    for i in range(3):
        link = link_factory(owner=test_user)
        links.append(link)
    return links

# Pytest Configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "auth: Authentication related tests")
    config.addinivalue_line("markers", "redis: Redis dependent tests")
    config.addinivalue_line("markers", "database: Database dependent tests")

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on location"""
    for item in items:
        # Mark based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Mark database tests
        if "database" in str(item.fspath) or "db_session" in item.fixturenames:
            item.add_marker(pytest.mark.database)
        
        # Mark Redis tests
        if "redis" in str(item.fspath) or "fake_redis" in item.fixturenames:
            item.add_marker(pytest.mark.redis)

# Test Utilities
class TestDataManager:
    """Utility class for managing test data"""
    
    @staticmethod
    def create_test_user(db_session, email="test@example.com", password="testpass123"):
        """Create a test user"""
        from app.auth import get_password_hash
        user = models.User(
            email=email,
            hashed_password=get_password_hash(password)
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    
    @staticmethod
    def create_test_link(db_session, user, target_url="https://example.com"):
        """Create a test link"""
        import secrets
        link = models.Link(
            short_key=secrets.token_urlsafe(8),
            target_url=target_url,
            owner_id=user.id
        )
        db_session.add(link)
        db_session.commit()
        db_session.refresh(link)
        return link

@pytest.fixture
def test_data_manager():
    """Test data manager utility"""
    return TestDataManager
