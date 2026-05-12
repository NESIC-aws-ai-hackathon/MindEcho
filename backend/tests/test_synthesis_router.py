import json
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.models import (
    ContextQuestion,
    ContextResponse,
    EmotionCandidate,
    EmotionSelection,
)
from app.data.models import GenerationSession, SessionStatus
from app.media.models import ImageAnalysisResult, MediaFile
from app.synthesis.models import GeneratedText


def _make_choices():
    return [
        {"label": "A", "text": "選択肢A"},
        {"label": "B", "text": "選択肢B"},
        {"label": "C", "text": "選択肢C"},
        {"label": "D", "text": "選択肢D"},
        {"label": "X", "text": "その他"},
    ]


@pytest_asyncio.fixture
async def synth_router_session(db_session: AsyncSession, auth_headers: dict):
    """Full session ready for synthesis via router."""
    from jose import jwt
    from app.core.config import settings

    token = auth_headers["Authorization"].split(" ")[1]
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    user_id = payload["sub"]

    session = GenerationSession(
        user_id=user_id, status=SessionStatus.EMOTIONS_SELECTED, media_type="image"
    )
    db_session.add(session)
    await db_session.flush()

    media = MediaFile(
        session_id=session.id, user_id=user_id, media_type="image",
        file_name="test.jpg", file_size=1000, mime_type="image/jpeg",
        s3_key=f"image/2026/05/synth-router-{session.id}.jpg",
    )
    db_session.add(media)
    await db_session.flush()

    analysis = ImageAnalysisResult(
        media_id=media.id, colors=["青"], composition="中央", mood="穏やか",
        subjects=["空"], atmosphere="晴れ", texture="滑らか",
        light_direction="上方", emotional_impression="開放感",
        image_category="photograph", style_characteristics="風景写真",
        raw_response="{}",
    )
    db_session.add(analysis)
    await db_session.flush()

    for i in range(1, 4):
        q = ContextQuestion(
            session_id=session.id, question_order=i,
            question_text=f"R設問{i}", choices=_make_choices(),
        )
        db_session.add(q)
    await db_session.flush()

    from sqlalchemy import select
    q_result = await db_session.execute(
        select(ContextQuestion).where(ContextQuestion.session_id == session.id)
    )
    for q in q_result.scalars().all():
        r = ContextResponse(question_id=q.id, session_id=session.id, selected_choice="B")
        db_session.add(r)
    await db_session.flush()

    c1 = EmotionCandidate(
        session_id=session.id, candidate_order=1,
        emotion_label="安らぎ", emotion_description="穏やかな感情",
    )
    db_session.add(c1)
    await db_session.flush()

    sel = EmotionSelection(candidate_id=c1.id, session_id=session.id)
    db_session.add(sel)
    await db_session.flush()
    await db_session.commit()

    return session


class TestGetFormats:
    @pytest.mark.asyncio
    async def test_200_no_auth(self, client: AsyncClient):
        response = await client.get("/api/synthesis/formats")
        assert response.status_code == 200
        data = response.json()
        assert len(data["formats"]) == 3
        ids = [f["id"] for f in data["formats"]]
        assert "sns" in ids
        assert "diary" in ids
        assert "review" in ids


class TestPostGenerate:
    @pytest.mark.asyncio
    async def test_201(self, client: AsyncClient, auth_headers, synth_router_session):
        session = synth_router_session

        with patch("app.synthesis.text_generator.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = "テスト生成文章です。SNS投稿用の短い文章。"
            response = await client.post(
                "/api/synthesis/generate",
                headers=auth_headers,
                json={"session_id": session.id, "output_format": "sns"},
            )

        assert response.status_code == 201
        data = response.json()
        assert data["output_format"] == "sns"
        assert data["generation_count"] == 1

    @pytest.mark.asyncio
    async def test_no_auth_401(self, client: AsyncClient, synth_router_session):
        session = synth_router_session
        response = await client.post(
            "/api/synthesis/generate",
            json={"session_id": session.id, "output_format": "sns"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_format_422(self, client: AsyncClient, auth_headers, synth_router_session):
        session = synth_router_session
        response = await client.post(
            "/api/synthesis/generate",
            headers=auth_headers,
            json={"session_id": session.id, "output_format": "invalid"},
        )
        assert response.status_code == 422


class TestGetSessionText:
    @pytest.mark.asyncio
    async def test_200(self, client: AsyncClient, auth_headers, db_session, synth_router_session):
        session = synth_router_session
        gt = GeneratedText(
            session_id=session.id, output_format="diary",
            generated_content="テスト日記文章", generation_count=1,
        )
        db_session.add(gt)
        await db_session.flush()
        await db_session.commit()

        response = await client.get(
            f"/api/synthesis/{session.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["generated_content"] == "テスト日記文章"

    @pytest.mark.asyncio
    async def test_404_not_generated(self, client: AsyncClient, auth_headers, synth_router_session):
        session = synth_router_session
        response = await client.get(
            f"/api/synthesis/{session.id}", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_no_auth_401(self, client: AsyncClient, synth_router_session):
        session = synth_router_session
        response = await client.get(f"/api/synthesis/{session.id}")
        assert response.status_code == 401
