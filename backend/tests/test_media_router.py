import json
from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import GenerationSession, SessionStatus
from app.media.models import MediaFile


@pytest_asyncio.fixture
async def session_for_upload(db_session: AsyncSession, auth_headers: dict) -> GenerationSession:
    """Create a session in 'created' status."""
    from jose import jwt
    from app.core.config import settings

    token = auth_headers["Authorization"].split(" ")[1]
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    user_id = payload["sub"]

    session = GenerationSession(user_id=user_id, status=SessionStatus.CREATED)
    db_session.add(session)
    await db_session.flush()
    return session


@pytest_asyncio.fixture
async def media_with_session(db_session: AsyncSession, session_for_upload: GenerationSession) -> MediaFile:
    """Create a media file linked to a session."""
    media = MediaFile(
        session_id=session_for_upload.id,
        user_id=session_for_upload.user_id,
        media_type="image",
        file_name="test.jpg",
        file_size=1024,
        mime_type="image/jpeg",
        s3_key="image/2026/05/test-router.jpg",
    )
    db_session.add(media)
    await db_session.flush()
    return media


def _make_image_bedrock_response():
    analysis = json.dumps({
        "colors": ["青"],
        "composition": "中央",
        "mood": "穏やか",
        "subjects": ["空"],
        "atmosphere": "晴れ",
        "texture": "滑らか",
        "light_direction": "上方",
        "emotional_impression": "開放感",
        "image_category": "photograph",
        "style_characteristics": "風景写真",
    }, ensure_ascii=False)
    return {
        "body": type("Body", (), {"read": lambda self: json.dumps({
            "content": [{"text": analysis}]
        }).encode()})()
    }


class TestUploadEndpoint:
    @pytest.mark.asyncio
    async def test_upload_image_201(self, client: AsyncClient, auth_headers, session_for_upload):
        with patch("app.media.image_analyzer.get_bedrock_client") as mock_client, \
             patch("app.core.s3_client.upload_file", new_callable=AsyncMock) as mock_s3:
            mock_client.return_value.invoke_model.return_value = _make_image_bedrock_response()
            mock_s3.return_value = "image/2026/05/test.jpg"

            response = await client.post(
                "/api/media/upload",
                headers=auth_headers,
                files={"file": ("test.jpg", b"fake image", "image/jpeg")},
                data={"session_id": session_for_upload.id},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["media_file"]["media_type"] == "image"
        assert data["image_analysis"] is not None
        assert data["image_analysis"]["image_category"] == "photograph"

    @pytest.mark.asyncio
    async def test_upload_invalid_mime_400(self, client: AsyncClient, auth_headers, session_for_upload):
        response = await client.post(
            "/api/media/upload",
            headers=auth_headers,
            files={"file": ("doc.pdf", b"fake pdf", "application/pdf")},
            data={"session_id": session_for_upload.id},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_no_auth_401(self, client: AsyncClient, session_for_upload):
        response = await client.post(
            "/api/media/upload",
            files={"file": ("test.jpg", b"fake", "image/jpeg")},
            data={"session_id": session_for_upload.id},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_upload_wrong_session_owner_403(self, client: AsyncClient, db_session, auth_headers):
        # Create session owned by another user
        other_session = GenerationSession(user_id="other-user", status=SessionStatus.CREATED)
        db_session.add(other_session)
        await db_session.flush()

        response = await client.post(
            "/api/media/upload",
            headers=auth_headers,
            files={"file": ("test.jpg", b"fake", "image/jpeg")},
            data={"session_id": other_session.id},
        )
        assert response.status_code == 403


class TestGetMediaEndpoint:
    @pytest.mark.asyncio
    async def test_get_media_200(self, client: AsyncClient, auth_headers, media_with_session):
        with patch("app.core.s3_client.generate_presigned_url") as mock_url:
            mock_url.return_value = "https://s3.example.com/presigned"

            response = await client.get(
                f"/api/media/{media_with_session.id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["media_file"]["id"] == media_with_session.id
        assert data["presigned_url"] == "https://s3.example.com/presigned"

    @pytest.mark.asyncio
    async def test_get_media_not_found_404(self, client: AsyncClient, auth_headers):
        response = await client.get(
            "/api/media/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_media_no_auth_401(self, client: AsyncClient, media_with_session):
        response = await client.get(f"/api/media/{media_with_session.id}")
        assert response.status_code in (401, 403)


class TestPresignedUrlEndpoint:
    @pytest.mark.asyncio
    async def test_presigned_url_200(self, client: AsyncClient, auth_headers, media_with_session):
        with patch("app.core.s3_client.generate_presigned_url") as mock_url:
            mock_url.return_value = "https://s3.example.com/download"

            response = await client.get(
                f"/api/media/{media_with_session.id}/presigned-url",
                headers=auth_headers,
            )

        assert response.status_code == 200
        assert response.json()["presigned_url"] == "https://s3.example.com/download"

    @pytest.mark.asyncio
    async def test_presigned_url_not_found(self, client: AsyncClient, auth_headers):
        response = await client.get(
            "/api/media/nonexistent/presigned-url",
            headers=auth_headers,
        )
        assert response.status_code == 404
