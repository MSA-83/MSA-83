"""Tests for the authentication service."""

import pytest
from fastapi import HTTPException

from backend.services.auth.auth_service import AuthConfig, AuthService


@pytest.fixture
def auth():
    return AuthService()


class TestAuthService:
    def test_register_user(self, auth):
        user = auth.register_user(
            email="test@example.com",
            password="securepassword123",
            tier="free",
        )

        assert user.email == "test@example.com"
        assert user.tier == "free"
        assert user.id.startswith("user-")

    def test_register_duplicate(self, auth):
        auth.register_user("test@example.com", "password123")

        with pytest.raises(HTTPException) as exc_info:
            auth.register_user("test@example.com", "password456")

        assert exc_info.value.status_code == 409

    def test_login_success(self, auth):
        auth.register_user("test@example.com", "securepassword123")

        tokens = auth.login("test@example.com", "securepassword123")

        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"

    def test_login_invalid_email(self, auth):
        with pytest.raises(HTTPException) as exc_info:
            auth.login("nonexistent@example.com", "password")

        assert exc_info.value.status_code == 401

    def test_login_wrong_password(self, auth):
        auth.register_user("test@example.com", "correctpassword")

        with pytest.raises(HTTPException) as exc_info:
            auth.login("test@example.com", "wrongpassword")

        assert exc_info.value.status_code == 401

    def test_token_decode_valid(self, auth):
        auth.register_user("test@example.com", "password123")
        tokens = auth.login("test@example.com", "password123")

        payload = auth.decode_token(tokens.access_token)

        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"

    def test_token_decode_expired(self, auth):
        from datetime import datetime, timedelta

        import jwt

        expired_token = jwt.encode(
            {
                "sub": "user-0001",
                "email": "test@example.com",
                "exp": datetime.utcnow() - timedelta(hours=1),
                "type": "access",
            },
            AuthConfig.SECRET_KEY,
            algorithm=AuthConfig.ALGORITHM,
        )

        with pytest.raises(HTTPException) as exc_info:
            auth.decode_token(expired_token)

        assert exc_info.value.status_code == 401

    def test_refresh_token(self, auth):
        auth.register_user("test@example.com", "password123")
        tokens = auth.login("test@example.com", "password123")

        new_tokens = auth.refresh_access_token(tokens.refresh_token)

        assert new_tokens.access_token is not None
        assert new_tokens.refresh_token is not None

    def test_get_user(self, auth):
        user = auth.register_user("test@example.com", "password123")
        retrieved = auth.get_user(user.id)

        assert retrieved is not None
        assert retrieved.email == "test@example.com"

    def test_get_user_not_found(self, auth):
        result = auth.get_user("user-9999")
        assert result is None

    def test_password_hashing(self, auth):
        password = "mysecretpassword"
        hashed = auth.hash_password(password)

        assert hashed != password
        assert auth.verify_password(password, hashed)
        assert not auth.verify_password("wrongpassword", hashed)
