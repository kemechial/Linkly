"""
Unit tests for authentication module
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta, UTC
from jose import jwt
from fastapi import HTTPException

from app import auth, models
from app.config import settings


class TestPasswordOperations:
    """Test password hashing and verification"""

    def test_get_password_hash(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = auth.get_password_hash(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")
        assert len(hashed) > 50

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = auth.get_password_hash(password)
        
        assert auth.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = auth.get_password_hash(password)
        
        assert auth.verify_password(wrong_password, hashed) is False

    def test_password_hash_uniqueness(self):
        """Test that same password generates different hashes"""
        password = "testpassword123"
        hash1 = auth.get_password_hash(password)
        hash2 = auth.get_password_hash(password)
        
        assert hash1 != hash2


class TestJWTTokens:
    """Test JWT token creation and validation"""

    def test_create_access_token(self):
        """Test access token creation"""
        data = {"sub": "test@example.com"}
        token = auth.create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 100
        
        # Decode and verify
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload

    def test_create_access_token_with_expiry(self):
        """Test access token with custom expiry"""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=15)
        token = auth.create_access_token(data, expires_delta)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        # Check expiry is approximately 15 minutes from now
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_time = datetime.now(UTC) + expires_delta
        time_diff = abs((exp_time - expected_time).total_seconds())
        
        assert time_diff < 5  # Within 5 seconds tolerance

    def test_decode_valid_token(self):
        """Test decoding valid token"""
        data = {"sub": "test@example.com", "user_id": 123}
        token = auth.create_access_token(data)
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == 123

    def test_decode_invalid_token(self):
        """Test decoding invalid token"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(jwt.JWTError):
            jwt.decode(invalid_token, settings.secret_key, algorithms=[settings.algorithm])

    def test_decode_expired_token(self):
        """Test decoding expired token"""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = auth.create_access_token(data, expires_delta)
        
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


class TestUserOperations:
    """Test user-related authentication operations"""

    def test_get_user_by_email_exists(self, db_session, test_data_manager):
        """Test getting user that exists"""
        # Create test user
        user = test_data_manager.create_test_user(db_session, "test@example.com")
        
        # Get user by email
        found_user = auth.get_user_by_email(db_session, "test@example.com")
        
        assert found_user is not None
        assert found_user.email == "test@example.com"
        assert found_user.id == user.id

    def test_get_user_by_email_not_exists(self, db_session):
        """Test getting user that doesn't exist"""
        found_user = auth.get_user_by_email(db_session, "nonexistent@example.com")
        
        assert found_user is None

    def test_authenticate_user_valid_credentials(self, db_session, test_data_manager):
        """Test user authentication with valid credentials"""
        # Create test user
        password = "testpassword123"
        user = test_data_manager.create_test_user(db_session, "test@example.com", password)
        
        # Authenticate user
        authenticated_user = auth.authenticate_user(
            db_session, "test@example.com", password
        )
        
        assert authenticated_user is not None
        assert authenticated_user.email == "test@example.com"

    def test_authenticate_user_invalid_email(self, db_session):
        """Test user authentication with invalid email"""
        result = auth.authenticate_user(
            db_session, "nonexistent@example.com", "password"
        )
        
        assert result is False

    def test_authenticate_user_invalid_password(self, db_session, test_data_manager):
        """Test user authentication with invalid password"""
        # Create test user
        user = test_data_manager.create_test_user(db_session, "test@example.com")
        
        result = auth.authenticate_user(
            db_session, "test@example.com", "wrongpassword"
        )
        
        assert result is False

# Note: The following tests are commented out because the functionality
# doesn't exist in the current auth module implementation
# 
# class TestPasswordValidation:
#     """Test password strength validation"""
# 
#     def test_validate_strong_password(self):
#         """Test validation of strong password"""
#         strong_password = "StrongP@ssw0rd123"
#         assert auth.validate_password_strength(strong_password) is True
# 
# class TestRateLimiting:
#     """Test rate limiting functionality"""
# 
#     def test_rate_limit_within_limit(self):
#         """Test rate limiting within allowed limits"""
#         identifier = "test_user_1"


@pytest.mark.integration
class TestGetCurrentUser:
    """Integration tests for get_current_user dependency"""

    def test_get_current_user_valid_token(self, db_session, test_data_manager):
        """Test getting current user with valid token"""
        # Create test user
        user = test_data_manager.create_test_user(db_session, "test@example.com")
        
        # Create token
        token = auth.create_access_token({"sub": user.email})
        
        # Get current user
        current_user = auth.get_current_user(token, db_session)
        
        assert current_user is not None
        assert current_user.email == user.email
        assert current_user.id == user.id

    def test_get_current_user_invalid_token(self, db_session):
        """Test getting current user with invalid token"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user(invalid_token, db_session)
        
        assert exc_info.value.status_code == 401

    def test_get_current_user_nonexistent_user(self, db_session):
        """Test getting current user for non-existent user"""
        # Create token for non-existent user
        token = auth.create_access_token({"sub": "nonexistent@example.com"})
        
        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user(token, db_session)
        
        assert exc_info.value.status_code == 401

    def test_get_current_user_missing_subject(self, db_session):
        """Test getting current user with token missing subject"""
        # Create token without subject
        token = auth.create_access_token({"user_id": 123})
        
        with pytest.raises(HTTPException) as exc_info:
            auth.get_current_user(token, db_session)
        
        assert exc_info.value.status_code == 401
