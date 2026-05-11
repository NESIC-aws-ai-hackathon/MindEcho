import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestListSessions:
    async def test_list_sessions_empty(self, client: AsyncClient, auth_headers: dict):
        response = await client.get("/api/data/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_sessions_after_create(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/data/sessions", headers=auth_headers)
        response = await client.get("/api/data/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "created"

    async def test_list_sessions_no_auth(self, client: AsyncClient):
        response = await client.get("/api/data/sessions")
        assert response.status_code == 403


@pytest.mark.asyncio
class TestCreateSession:
    async def test_create_session_success(self, client: AsyncClient, auth_headers: dict):
        response = await client.post("/api/data/sessions", headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "created"
        assert data["media_type"] is None

    async def test_create_session_limit(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/data/sessions", headers=auth_headers)
        response = await client.post("/api/data/sessions", headers=auth_headers)
        assert response.status_code == 409


@pytest.mark.asyncio
class TestDeleteSession:
    async def test_delete_session_success(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post("/api/data/sessions", headers=auth_headers)
        session_id = create_resp.json()["id"]

        response = await client.delete(
            f"/api/data/sessions/{session_id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert "削除" in response.json()["message"]

    async def test_delete_session_not_found(self, client: AsyncClient, auth_headers: dict):
        response = await client.delete(
            "/api/data/sessions/nonexistent-id", headers=auth_headers
        )
        assert response.status_code == 404

    async def test_delete_session_no_auth(self, client: AsyncClient):
        response = await client.delete("/api/data/sessions/some-id")
        assert response.status_code == 403
