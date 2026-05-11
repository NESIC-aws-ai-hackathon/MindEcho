import json
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.models import ContextQuestion, ContextResponse, EmotionCandidate, FreeTextInput
from app.data.models import GenerationSession, SessionStatus


def _make_choices():
    return [
        {"label": "A", "text": "選択肢A"},
        {"label": "B", "text": "選択肢B"},
        {"label": "C", "text": "選択肢C"},
        {"label": "D", "text": "選択肢D"},
        {"label": "X", "text": "その他"},
    ]


@pytest_asyncio.fixture
async def cog_session(db_session: AsyncSession, auth_headers: dict):
    """Session with media_uploaded status and 3 questions."""
    from jose import jwt
    from app.core.config import settings

    token = auth_headers["Authorization"].split(" ")[1]
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    user_id = payload["sub"]

    session = GenerationSession(user_id=user_id, status=SessionStatus.MEDIA_UPLOADED, media_type="image")
    db_session.add(session)
    await db_session.flush()

    questions = []
    for i in range(1, 4):
        q = ContextQuestion(
            session_id=session.id, question_order=i,
            question_text=f"Router設問{i}", choices=_make_choices(),
        )
        db_session.add(q)
        questions.append(q)
    await db_session.flush()

    return session, questions


class TestPostResponses:
    @pytest.mark.asyncio
    async def test_201(self, client: AsyncClient, auth_headers, cog_session):
        session, questions = cog_session
        body = {
            "session_id": session.id,
            "responses": [
                {"question_id": q.id, "selected_choice": "A"} for q in questions
            ],
        }
        response = await client.post("/api/cognitive/responses", headers=auth_headers, json=body)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_no_auth_401(self, client: AsyncClient, cog_session):
        session, questions = cog_session
        body = {
            "session_id": session.id,
            "responses": [{"question_id": q.id, "selected_choice": "A"} for q in questions],
        }
        response = await client.post("/api/cognitive/responses", json=body)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_incomplete_422(self, client: AsyncClient, auth_headers, cog_session):
        session, questions = cog_session
        body = {
            "session_id": session.id,
            "responses": [{"question_id": questions[0].id, "selected_choice": "A"}],
        }
        response = await client.post("/api/cognitive/responses", headers=auth_headers, json=body)
        assert response.status_code == 422


class TestPostFreeText:
    @pytest.mark.asyncio
    async def test_201(self, client: AsyncClient, auth_headers, db_session, cog_session):
        session, questions = cog_session

        # Submit responses first
        for q in questions:
            r = ContextResponse(question_id=q.id, session_id=session.id, selected_choice="B")
            db_session.add(r)
        await db_session.flush()
        await db_session.commit()

        body = {"session_id": session.id, "content": "テスト自由記述です"}
        response = await client.post("/api/cognitive/free-text", headers=auth_headers, json=body)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_no_auth_401(self, client: AsyncClient, cog_session):
        session, _ = cog_session
        body = {"session_id": session.id, "content": "テスト"}
        response = await client.post("/api/cognitive/free-text", json=body)
        assert response.status_code == 401


class TestPostCompleteQuestions:
    @pytest.mark.asyncio
    async def test_201(self, client: AsyncClient, auth_headers, db_session, cog_session):
        session, questions = cog_session

        for q in questions:
            r = ContextResponse(question_id=q.id, session_id=session.id, selected_choice="C")
            db_session.add(r)
        await db_session.flush()
        await db_session.commit()

        with patch("app.cognitive.emotion_generator.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = json.dumps({
                "emotions": [
                    {"emotion_label": f"E{i}", "emotion_description": f"D{i}"} for i in range(3)
                ]
            }, ensure_ascii=False)

            body = {"session_id": session.id}
            response = await client.post("/api/cognitive/complete-questions", headers=auth_headers, json=body)

        assert response.status_code == 201
        data = response.json()
        assert len(data["candidates"]) == 3


class TestPostEmotions:
    @pytest.mark.asyncio
    async def test_201(self, client: AsyncClient, auth_headers, db_session, cog_session):
        session, questions = cog_session
        session.status = SessionStatus.QUESTIONS_ANSWERED
        await db_session.flush()

        c1 = EmotionCandidate(session_id=session.id, candidate_order=1, emotion_label="E1", emotion_description="D1")
        c2 = EmotionCandidate(session_id=session.id, candidate_order=2, emotion_label="E2", emotion_description="D2")
        db_session.add_all([c1, c2])
        await db_session.flush()
        await db_session.commit()

        body = {"session_id": session.id, "candidate_ids": [c1.id]}
        response = await client.post("/api/cognitive/emotions", headers=auth_headers, json=body)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_empty_selection_422(self, client: AsyncClient, auth_headers, db_session, cog_session):
        session, _ = cog_session
        session.status = SessionStatus.QUESTIONS_ANSWERED
        await db_session.flush()
        await db_session.commit()

        body = {"session_id": session.id, "candidate_ids": []}
        response = await client.post("/api/cognitive/emotions", headers=auth_headers, json=body)
        assert response.status_code == 422


class TestGetQuestions:
    @pytest.mark.asyncio
    async def test_200(self, client: AsyncClient, auth_headers, cog_session):
        session, questions = cog_session
        response = await client.get(f"/api/cognitive/questions/{session.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["questions"]) == 3

    @pytest.mark.asyncio
    async def test_no_auth_401(self, client: AsyncClient, cog_session):
        session, _ = cog_session
        response = await client.get(f"/api/cognitive/questions/{session.id}")
        assert response.status_code == 401


class TestGetEmotions:
    @pytest.mark.asyncio
    async def test_200(self, client: AsyncClient, auth_headers, db_session, cog_session):
        session, _ = cog_session
        c = EmotionCandidate(session_id=session.id, candidate_order=1, emotion_label="E1", emotion_description="D1")
        db_session.add(c)
        await db_session.flush()
        await db_session.commit()

        response = await client.get(f"/api/cognitive/emotions/{session.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["candidates"]) == 1
        assert data["candidates"][0]["is_selected"] is False
