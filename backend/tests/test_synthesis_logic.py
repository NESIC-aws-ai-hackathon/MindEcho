import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.models import (
    ContextQuestion,
    ContextResponse,
    EmotionCandidate,
    EmotionSelection,
)
from app.core.exceptions import NotFoundError, ValidationError
from app.data.models import GenerationSession, SessionStatus
from app.media.models import ImageAnalysisResult, MediaFile
from app.synthesis.logic import generate_or_regenerate, get_generated_text
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
async def synth_session(db_session: AsyncSession):
    """Full session ready for synthesis (emotions_selected status)."""
    from app.auth.models import User

    user = User(email="synth@test.com", password_hash="hashed")
    db_session.add(user)
    await db_session.flush()

    session = GenerationSession(
        user_id=user.id, status=SessionStatus.EMOTIONS_SELECTED, media_type="image"
    )
    db_session.add(session)
    await db_session.flush()

    # Media + analysis
    media = MediaFile(
        session_id=session.id, user_id=user.id, media_type="image",
        file_name="test.jpg", file_size=1000, mime_type="image/jpeg",
        s3_key="image/2026/05/synth.jpg",
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

    # Questions + responses
    for i in range(1, 4):
        q = ContextQuestion(
            session_id=session.id, question_order=i,
            question_text=f"設問{i}", choices=_make_choices(),
        )
        db_session.add(q)
    await db_session.flush()

    q_result = await db_session.execute(
        __import__("sqlalchemy").select(ContextQuestion).where(
            ContextQuestion.session_id == session.id
        )
    )
    questions = list(q_result.scalars().all())
    for q in questions:
        r = ContextResponse(
            question_id=q.id, session_id=session.id, selected_choice="A"
        )
        db_session.add(r)
    await db_session.flush()

    # Emotion candidates + selection
    c1 = EmotionCandidate(
        session_id=session.id, candidate_order=1,
        emotion_label="懐かしさ", emotion_description="過去を振り返る",
    )
    db_session.add(c1)
    await db_session.flush()

    sel = EmotionSelection(candidate_id=c1.id, session_id=session.id)
    db_session.add(sel)
    await db_session.flush()

    return user, session


class TestGenerateOrRegenerate:
    @pytest.mark.asyncio
    async def test_first_generation(self, db_session, synth_session):
        user, session = synth_session

        with patch("app.synthesis.text_generator.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = "テスト生成文章です。" * 10
            result = await generate_or_regenerate(db_session, session.id, user.id, "sns")

        assert result.generation_count == 1
        assert result.output_format == "sns"
        assert session.status == SessionStatus.GENERATED

    @pytest.mark.asyncio
    async def test_regeneration(self, db_session, synth_session):
        user, session = synth_session

        with patch("app.synthesis.text_generator.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = "1回目の生成"
            await generate_or_regenerate(db_session, session.id, user.id, "sns")

            mock.return_value = "2回目の生成"
            result = await generate_or_regenerate(db_session, session.id, user.id, "diary")

        assert result.generation_count == 2
        assert result.output_format == "diary"
        assert result.generated_content == "2回目の生成"

    @pytest.mark.asyncio
    async def test_max_generation_limit(self, db_session, synth_session):
        user, session = synth_session

        # Create a generated text at count=10
        gt = GeneratedText(
            session_id=session.id, output_format="sns",
            generated_content="テスト", generation_count=10,
        )
        db_session.add(gt)
        session.status = SessionStatus.GENERATED
        await db_session.flush()

        with pytest.raises(ValidationError):
            await generate_or_regenerate(db_session, session.id, user.id, "sns")

    @pytest.mark.asyncio
    async def test_wrong_status_fails(self, db_session, synth_session):
        user, session = synth_session
        session.status = SessionStatus.MEDIA_UPLOADED
        await db_session.flush()

        with pytest.raises(ValidationError):
            await generate_or_regenerate(db_session, session.id, user.id, "sns")


class TestGetGeneratedText:
    @pytest.mark.asyncio
    async def test_success(self, db_session, synth_session):
        user, session = synth_session
        gt = GeneratedText(
            session_id=session.id, output_format="sns",
            generated_content="テスト文章", generation_count=1,
        )
        db_session.add(gt)
        await db_session.flush()

        result = await get_generated_text(db_session, session.id, user.id)
        assert result.generated_content == "テスト文章"

    @pytest.mark.asyncio
    async def test_not_found(self, db_session, synth_session):
        user, session = synth_session
        with pytest.raises(NotFoundError):
            await get_generated_text(db_session, session.id, user.id)
