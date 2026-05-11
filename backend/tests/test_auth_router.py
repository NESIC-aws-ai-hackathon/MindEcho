import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "password123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={"email": "dup@example.com", "password": "password123"},
        )
        response = await client.post(
            "/api/auth/register",
            json={"email": "dup@example.com", "password": "password456"},
        )
        assert response.status_code == 409

    async def test_register_invalid_email(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={"email": "short@example.com", "password": "1234567"},
        )
        assert response.status_code == 422

    async def test_register_email_normalized_to_lowercase(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/register",
            json={"email": "TEST@Example.COM", "password": "password123"},
        )
        assert response.status_code == 201


@pytest.mark.asyncio
class TestLogin:
    async def test_login_success(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={"email": "login@example.com", "password": "password123"},
        )
        response = await client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={"email": "wrong@example.com", "password": "password123"},
        )
        response = await client.post(
            "/api/auth/login",
            json={"email": "wrong@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_email(self, client: AsyncClient):
        response = await client.post(
            "/api/auth/login",
            json={"email": "noone@example.com", "password": "password123"},
        )
        assert response.status_code == 401

    async def test_login_unified_error_message(self, client: AsyncClient):
        """Both wrong password and nonexistent email return same message."""
        r1 = await client.post(
            "/api/auth/login",
            json={"email": "noone@example.com", "password": "pass"},
        )
        await client.post(
            "/api/auth/register",
            json={"email": "exists@example.com", "password": "password123"},
        )
        r2 = await client.post(
            "/api/auth/login",
            json={"email": "exists@example.com", "password": "wrong"},
        )
        assert r1.json()["detail"]["error"]["message"] == r2.json()["detail"]["error"]["message"]


@pytest.mark.asyncio
class TestDeleteAccount:
    async def test_delete_account_success(self, client: AsyncClient, auth_headers: dict):
        response = await client.delete("/api/auth/account", headers=auth_headers)
        assert response.status_code == 200
        assert "削除" in response.json()["message"]

    async def test_delete_account_no_auth(self, client: AsyncClient):
        response = await client.delete("/api/auth/account")
        assert response.status_code == 403  # No bearer token → HTTPBearer returns 403
