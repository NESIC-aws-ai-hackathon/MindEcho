import pytest

from app.auth.logic import create_access_token, hash_password, verify_password


class TestPasswordHashing:
    def test_hash_password_returns_bcrypt_hash(self):
        hashed = hash_password("mypassword")
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60

    def test_verify_password_correct(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False


class TestJWT:
    def test_create_access_token_returns_string(self):
        token = create_access_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_sub(self):
        from jose import jwt

        from app.core.config import settings

        token = create_access_token("user-456")
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "user-456"
        assert "exp" in payload
        assert "iat" in payload
