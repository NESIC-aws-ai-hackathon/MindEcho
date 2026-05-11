import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.models import ContextQuestion, ContextResponse, EmotionCandidate, FreeTextInput
from app.cognitive.logic import (
    complete_questions,
    get_emotions,
    get_questions,
    select_emotions,
    submit_free_text,
    submit_responses,
)
from app.core.exceptions import ValidationError
from app.data.models import GenerationSession, SessionStatus
from app.media.models import ImageAnalysisResult, MediaFile


def _make_choices():
    return [
        {"label": "A", "text": "選択肢A"},
        {"label": "B", "text": "選択肢B"},
        {"label": "C", "text": "選択肢C"},
        {"label": "D", "text": "選択肢D"},
        {"label": "X", "text": "その他"},
    ]


@pytest_asyncio.fixture
async def user_and_session(db_session: AsyncSession):
    """Create a user and session in media_uploaded status with questions."""
    from app.auth.models import User

    user = User(email="cog@test.com", password_hash="hashed")
    db_session.add(user)
    await db_session.flush()

    session = GenerationSession(user_id=user.id, status=SessionStatus.MEDIA_UPLOADED, media_type="image")
    db_session.add(session)
    await db_session.flush()

    # Create media + analysis
    media = MediaFile(
        session_id=session.id, user_id=user.id, media_type="image",
        file_name="test.jpg", file_size=1000, mime_type="image/jpeg",
        s3_key="image/2026/05/test.jpg",
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

    # Create 3 questions
    questions = []
    for i in range(1, 4):
        q = ContextQuestion(
            session_id=session.id, question_order=i,
            question_text=f"テスト設問{i}", choices=_make_choices(),
        )
        db_session.add(q)
        questions.append(q)
    await db_session.flush()

    return user, session, questions


class TestSubmitResponses:
    @pytest.mark.asyncio
    async def test_success(self, db_session, user_and_session):
        user, session, questions = user_and_session

        class Resp:
            def __init__(self, qid, choice, text=None):
                self.question_id = qid
                self.selected_choice = choice
                self.other_text = text

        responses = [Resp(q.id, "A") for q in questions]
        result = await submit_responses(db_session, session.id, user.id, responses)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_wrong_status_fails(self, db_session, user_and_session):
        user, session, questions = user_and_session
        session.status = SessionStatus.QUESTIONS_ANSWERED
        await db_session.flush()

        class Resp:
            def __init__(self, qid):
                self.question_id = qid
                self.selected_choice = "A"
                self.other_text = None

        with pytest.raises(ValidationError):
            await submit_responses(db_session, session.id, user.id, [Resp(q.id) for q in questions])

    @pytest.mark.asyncio
    async def test_incomplete_responses_fails(self, db_session, user_and_session):
        user, session, questions = user_and_session

        class Resp:
            def __init__(self, qid):
                self.question_id = qid
                self.selected_choice = "A"
                self.other_text = None

        # Only answer 2 out of 3
        with pytest.raises(ValidationError):
            await submit_responses(db_session, session.id, user.id, [Resp(questions[0].id), Resp(questions[1].id)])

    @pytest.mark.asyncio
    async def test_other_requires_text(self, db_session, user_and_session):
        user, session, questions = user_and_session

        class Resp:
            def __init__(self, qid, choice, text=None):
                self.question_id = qid
                self.selected_choice = choice
                self.other_text = text

        responses = [Resp(questions[0].id, "X", None), Resp(questions[1].id, "A"), Resp(questions[2].id, "B")]
        with pytest.raises(ValidationError):
            await submit_responses(db_session, session.id, user.id, responses)


class TestSubmitFreeText:
    @pytest.mark.asyncio
    async def test_success_after_responses(self, db_session, user_and_session):
        user, session, questions = user_and_session

        # First submit responses
        for q in questions:
            r = ContextResponse(question_id=q.id, session_id=session.id, selected_choice="A")
            db_session.add(r)
        await db_session.flush()

        result = await submit_free_text(db_session, session.id, user.id, "テスト自由記述")
        assert result.content == "テスト自由記述"

    @pytest.mark.asyncio
    async def test_duplicate_fails(self, db_session, user_and_session):
        user, session, questions = user_and_session

        for q in questions:
            r = ContextResponse(question_id=q.id, session_id=session.id, selected_choice="A")
            db_session.add(r)
        await db_session.flush()

        await submit_free_text(db_session, session.id, user.id, "1回目")
        with pytest.raises(ValidationError):
            await submit_free_text(db_session, session.id, user.id, "2回目")

    @pytest.mark.asyncio
    async def test_without_responses_fails(self, db_session, user_and_session):
        user, session, questions = user_and_session
        with pytest.raises(ValidationError):
            await submit_free_text(db_session, session.id, user.id, "テスト")


class TestCompleteQuestions:
    @pytest.mark.asyncio
    async def test_success(self, db_session, user_and_session):
        user, session, questions = user_and_session

        for q in questions:
            r = ContextResponse(question_id=q.id, session_id=session.id, selected_choice="B")
            db_session.add(r)
        await db_session.flush()

        with patch("app.cognitive.emotion_generator.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = '{"emotions": [{"emotion_label": "E1", "emotion_description": "D1"}, {"emotion_label": "E2", "emotion_description": "D2"}, {"emotion_label": "E3", "emotion_description": "D3"}]}'
            candidates = await complete_questions(db_session, session.id, user.id)

        assert len(candidates) == 3
        assert session.status == SessionStatus.QUESTIONS_ANSWERED

    @pytest.mark.asyncio
    async def test_without_responses_fails(self, db_session, user_and_session):
        user, session, questions = user_and_session
        with pytest.raises(ValidationError):
            await complete_questions(db_session, session.id, user.id)


class TestSelectEmotions:
    @pytest.mark.asyncio
    async def test_success(self, db_session, user_and_session):
        user, session, questions = user_and_session
        session.status = SessionStatus.QUESTIONS_ANSWERED
        await db_session.flush()

        c1 = EmotionCandidate(session_id=session.id, candidate_order=1, emotion_label="E1", emotion_description="D1")
        c2 = EmotionCandidate(session_id=session.id, candidate_order=2, emotion_label="E2", emotion_description="D2")
        db_session.add_all([c1, c2])
        await db_session.flush()

        selections = await select_emotions(db_session, session.id, user.id, [c1.id, c2.id])
        assert len(selections) == 2
        assert session.status == SessionStatus.EMOTIONS_SELECTED

    @pytest.mark.asyncio
    async def test_wrong_status_fails(self, db_session, user_and_session):
        user, session, questions = user_and_session
        # status is still MEDIA_UPLOADED
        with pytest.raises(ValidationError):
            await select_emotions(db_session, session.id, user.id, ["fake-id"])

    @pytest.mark.asyncio
    async def test_invalid_candidate_fails(self, db_session, user_and_session):
        user, session, questions = user_and_session
        session.status = SessionStatus.QUESTIONS_ANSWERED
        await db_session.flush()

        with pytest.raises(ValidationError):
            await select_emotions(db_session, session.id, user.id, ["nonexistent-id"])


class TestGetQuestions:
    @pytest.mark.asyncio
    async def test_returns_questions(self, db_session, user_and_session):
        user, session, questions = user_and_session
        result_q, result_r = await get_questions(db_session, session.id, user.id)
        assert len(result_q) == 3
        assert len(result_r) == 0


class TestGetEmotions:
    @pytest.mark.asyncio
    async def test_returns_candidates(self, db_session, user_and_session):
        user, session, questions = user_and_session
        c = EmotionCandidate(session_id=session.id, candidate_order=1, emotion_label="E1", emotion_description="D1")
        db_session.add(c)
        await db_session.flush()

        candidates, selections = await get_emotions(db_session, session.id, user.id)
        assert len(candidates) == 1
        assert len(selections) == 0
