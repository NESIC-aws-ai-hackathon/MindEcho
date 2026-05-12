import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.models import (
    ContextQuestion,
    ContextResponse,
    EmotionCandidate,
    EmotionSelection,
    FreeTextInput,
)
from app.core.exceptions import NotFoundError, ForbiddenError, ValidationError
from app.data.models import GenerationSession, SessionStatus
from app.media.models import ImageAnalysisResult, MediaFile, MusicAnalysisResult
from app.synthesis.models import GeneratedText, OUTPUT_FORMAT_INFO
from app.synthesis.text_generator import (
    build_common_context,
    build_prompt,
    generate_text,
)

logger = logging.getLogger(__name__)

MAX_GENERATION_COUNT = 10


async def _get_session(db: AsyncSession, session_id: str, user_id: str) -> GenerationSession:
    """Get and validate session ownership."""
    result = await db.execute(
        select(GenerationSession).where(GenerationSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise NotFoundError("セッションが見つかりません")
    if session.user_id != user_id:
        raise ForbiddenError("このセッションへのアクセス権限がありません")
    return session


async def _load_context(db: AsyncSession, session_id: str):
    """Load all context data for prompt building."""
    # Media + Analysis
    media_result = await db.execute(
        select(MediaFile).where(MediaFile.session_id == session_id)
    )
    media_file = media_result.scalar_one_or_none()

    image_analysis = None
    music_analysis = None
    if media_file:
        if media_file.media_type == "image":
            r = await db.execute(
                select(ImageAnalysisResult).where(ImageAnalysisResult.media_id == media_file.id)
            )
            image_analysis = r.scalar_one_or_none()
        else:
            r = await db.execute(
                select(MusicAnalysisResult).where(MusicAnalysisResult.media_id == media_file.id)
            )
            music_analysis = r.scalar_one_or_none()

    # Questions + Responses
    q_result = await db.execute(
        select(ContextQuestion)
        .where(ContextQuestion.session_id == session_id)
        .order_by(ContextQuestion.question_order)
    )
    questions = list(q_result.scalars().all())

    r_result = await db.execute(
        select(ContextResponse).where(ContextResponse.session_id == session_id)
    )
    responses = list(r_result.scalars().all())

    # Free text
    ft_result = await db.execute(
        select(FreeTextInput).where(FreeTextInput.session_id == session_id)
    )
    free_text_record = ft_result.scalar_one_or_none()
    free_text = free_text_record.content if free_text_record else None

    # Emotions
    ec_result = await db.execute(
        select(EmotionCandidate)
        .where(EmotionCandidate.session_id == session_id)
        .order_by(EmotionCandidate.candidate_order)
    )
    candidates = list(ec_result.scalars().all())

    es_result = await db.execute(
        select(EmotionSelection).where(EmotionSelection.session_id == session_id)
    )
    selections = list(es_result.scalars().all())

    return image_analysis, music_analysis, questions, responses, free_text, candidates, selections


async def generate_or_regenerate(
    db: AsyncSession, session_id: str, user_id: str, output_format: str
) -> GeneratedText:
    """Generate or regenerate text for a session."""
    session = await _get_session(db, session_id, user_id)

    if session.status not in (SessionStatus.EMOTIONS_SELECTED, SessionStatus.GENERATED):
        raise ValidationError("この操作は現在のセッション状態では実行できません")

    # Check existing generated text
    existing_result = await db.execute(
        select(GeneratedText).where(GeneratedText.session_id == session_id)
    )
    existing = existing_result.scalar_one_or_none()

    if existing and existing.generation_count >= MAX_GENERATION_COUNT:
        raise ValidationError("再生成回数の上限に達しました（最大10回）")

    # Load all context
    (
        image_analysis, music_analysis,
        questions, responses, free_text,
        candidates, selections,
    ) = await _load_context(db, session_id)

    # Build prompt and generate
    common_context = build_common_context(
        image_analysis=image_analysis,
        music_analysis=music_analysis,
        responses=responses,
        questions=questions,
        free_text=free_text,
        candidates=candidates,
        selections=selections,
    )
    prompt = build_prompt(output_format, common_context)
    generated_content = await generate_text(prompt)

    if existing:
        # Regenerate: update existing record
        existing.generated_content = generated_content
        existing.output_format = output_format
        existing.generation_count += 1
        existing.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return existing
    else:
        # First generation: create new record
        generated = GeneratedText(
            session_id=session_id,
            output_format=output_format,
            generated_content=generated_content,
            generation_count=1,
        )
        db.add(generated)

        # Update session status
        session.status = SessionStatus.GENERATED
        await db.flush()
        return generated


async def get_generated_text(
    db: AsyncSession, session_id: str, user_id: str
) -> GeneratedText:
    """Get generated text for a session."""
    await _get_session(db, session_id, user_id)

    result = await db.execute(
        select(GeneratedText).where(GeneratedText.session_id == session_id)
    )
    generated = result.scalar_one_or_none()
    if generated is None:
        raise NotFoundError("生成テキストが見つかりません")
    return generated


def get_formats() -> list[dict]:
    """Return output format information."""
    return OUTPUT_FORMAT_INFO
