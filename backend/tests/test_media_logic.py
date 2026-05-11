import json
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.models import GenerationSession, SessionStatus
from app.media.logic import get_media_detail, get_presigned_url, upload_and_analyze
from app.media.models import ImageAnalysisResult, MediaFile, MusicAnalysisResult


@pytest_asyncio.fixture
async def session_for_upload(db_session: AsyncSession, auth_headers: dict) -> GenerationSession:
    """Create a session in 'created' status for upload tests."""
    # Extract user_id from the token
    from jose import jwt
    from app.core.config import settings

    token = auth_headers["Authorization"].split(" ")[1]
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    user_id = payload["sub"]

    session = GenerationSession(user_id=user_id, status=SessionStatus.CREATED)
    db_session.add(session)
    await db_session.flush()
    return session


def _make_image_analysis_response():
    return json.dumps({
        "colors": ["深い青", "白"],
        "composition": "中央配置",
        "mood": "穏やか",
        "subjects": ["空", "雲"],
        "atmosphere": "晴れた日の午後",
        "texture": "滑らか",
        "light_direction": "上方からの自然光",
        "emotional_impression": "開放感を感じる",
        "image_category": "photograph",
        "style_characteristics": "風景写真、広角レンズ",
    }, ensure_ascii=False)


def _make_music_analysis_response():
    return json.dumps({
        "bpm": 120,
        "key": "C major",
        "chord_progression": "I-V-vi-IV",
        "rhythm": "軽快な4拍子",
        "tempo": "アップテンポ",
        "mood": "高揚感",
        "energy_level": "高い",
        "emotional_impression": "元気が出る楽曲",
    }, ensure_ascii=False)


class TestUploadAndAnalyze:
    @pytest.mark.asyncio
    async def test_image_upload_success(self, db_session, session_for_upload):
        mock_bedrock_response = {
            "body": type("Body", (), {"read": lambda self: json.dumps({
                "content": [{"text": _make_image_analysis_response()}]
            }).encode()})()
        }

        with patch("app.media.image_analyzer.get_bedrock_client") as mock_client, \
             patch("app.core.s3_client.upload_file", new_callable=AsyncMock) as mock_s3:
            mock_client.return_value.invoke_model.return_value = mock_bedrock_response
            mock_s3.return_value = "image/2026/05/test.jpg"

            media_file, img_analysis, music_analysis = await upload_and_analyze(
                db=db_session,
                session_id=session_for_upload.id,
                user_id=session_for_upload.user_id,
                file_data=b"fake image data",
                file_name="test.jpg",
                mime_type="image/jpeg",
            )

        assert media_file.media_type == "image"
        assert media_file.file_name == "test.jpg"
        assert img_analysis is not None
        assert img_analysis.image_category == "photograph"
        assert music_analysis is None

        # Session should be updated
        await db_session.refresh(session_for_upload)
        assert session_for_upload.status == SessionStatus.MEDIA_UPLOADED

    @pytest.mark.asyncio
    async def test_music_upload_success(self, db_session, session_for_upload):
        with patch("app.media.music_analyzer.invoke_model", new_callable=AsyncMock) as mock_invoke, \
             patch("app.core.s3_client.upload_file", new_callable=AsyncMock) as mock_s3:
            mock_invoke.return_value = _make_music_analysis_response()
            mock_s3.return_value = "music/2026/05/test.mp3"

            media_file, img_analysis, music_analysis = await upload_and_analyze(
                db=db_session,
                session_id=session_for_upload.id,
                user_id=session_for_upload.user_id,
                file_data=b"fake mp3 data",
                file_name="test.mp3",
                mime_type="audio/mpeg",
            )

        assert media_file.media_type == "music"
        assert music_analysis is not None
        assert music_analysis.bpm == 120
        assert music_analysis.key == "C major"
        assert img_analysis is None

    @pytest.mark.asyncio
    async def test_session_not_found(self, db_session, session_for_upload):
        with pytest.raises(Exception) as exc_info:
            await upload_and_analyze(
                db=db_session,
                session_id="nonexistent-id",
                user_id=session_for_upload.user_id,
                file_data=b"data",
                file_name="test.jpg",
                mime_type="image/jpeg",
            )
        assert "見つかりません" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_wrong_owner(self, db_session, session_for_upload):
        with pytest.raises(Exception) as exc_info:
            await upload_and_analyze(
                db=db_session,
                session_id=session_for_upload.id,
                user_id="other-user-id",
                file_data=b"data",
                file_name="test.jpg",
                mime_type="image/jpeg",
            )
        assert "権限" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_session_wrong_status(self, db_session, session_for_upload):
        session_for_upload.status = SessionStatus.MEDIA_UPLOADED
        await db_session.flush()

        with pytest.raises(Exception) as exc_info:
            await upload_and_analyze(
                db=db_session,
                session_id=session_for_upload.id,
                user_id=session_for_upload.user_id,
                file_data=b"data",
                file_name="test.jpg",
                mime_type="image/jpeg",
            )
        assert "すでにメディア" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_analysis_failure_rollbacks_s3(self, db_session, session_for_upload):
        with patch("app.media.image_analyzer.get_bedrock_client") as mock_client, \
             patch("app.core.s3_client.upload_file", new_callable=AsyncMock) as mock_s3_upload, \
             patch("app.core.s3_client.delete_file", new_callable=AsyncMock) as mock_s3_delete:
            mock_client.return_value.invoke_model.side_effect = RuntimeError("Bedrock down")
            mock_s3_upload.return_value = "image/2026/05/test.jpg"

            with pytest.raises(Exception) as exc_info:
                await upload_and_analyze(
                    db=db_session,
                    session_id=session_for_upload.id,
                    user_id=session_for_upload.user_id,
                    file_data=b"data",
                    file_name="test.jpg",
                    mime_type="image/jpeg",
                )

            # S3 file should be cleaned up
            mock_s3_delete.assert_called_once()


class TestGetMediaDetail:
    @pytest.mark.asyncio
    async def test_get_existing_media(self, db_session, session_for_upload):
        # Create a media file directly
        media = MediaFile(
            session_id=session_for_upload.id,
            user_id=session_for_upload.user_id,
            media_type="image",
            file_name="test.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            s3_key="image/2026/05/test.jpg",
        )
        db_session.add(media)
        await db_session.flush()

        mf, img, music = await get_media_detail(db_session, media.id, session_for_upload.user_id)
        assert mf.id == media.id
        assert mf.file_name == "test.jpg"

    @pytest.mark.asyncio
    async def test_not_found(self, db_session):
        with pytest.raises(Exception):
            await get_media_detail(db_session, "nonexistent", "user1")

    @pytest.mark.asyncio
    async def test_wrong_owner(self, db_session, session_for_upload):
        media = MediaFile(
            session_id=session_for_upload.id,
            user_id=session_for_upload.user_id,
            media_type="image",
            file_name="test.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            s3_key="image/2026/05/test2.jpg",
        )
        db_session.add(media)
        await db_session.flush()

        with pytest.raises(Exception):
            await get_media_detail(db_session, media.id, "other-user")


class TestGetPresignedUrl:
    @pytest.mark.asyncio
    async def test_presigned_url(self, db_session, session_for_upload):
        media = MediaFile(
            session_id=session_for_upload.id,
            user_id=session_for_upload.user_id,
            media_type="image",
            file_name="test.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            s3_key="image/2026/05/test3.jpg",
        )
        db_session.add(media)
        await db_session.flush()

        with patch("app.core.s3_client.generate_presigned_url") as mock_url:
            mock_url.return_value = "https://s3.example.com/presigned"
            url = await get_presigned_url(db_session, media.id, session_for_upload.user_id)

        assert url == "https://s3.example.com/presigned"
