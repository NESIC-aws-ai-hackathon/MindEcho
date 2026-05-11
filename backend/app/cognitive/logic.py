import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.emotion_generator import generate_emotions
from app.cognitive.models import (
    ContextQuestion,
    ContextResponse,
    EmotionCandidate,
    EmotionSelection,
    FreeTextInput,
)
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.data.models import GenerationSession, SessionStatus
from app.media.models import ImageAnalysisResult, MediaFile, MusicAnalysisResult

logger = logging.getLogger(__name__)


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


async def submit_responses(
    db: AsyncSession, session_id: str, user_id: str, responses: list
) -> list[ContextResponse]:
    """Submit responses to all context questions.

    Args:
        responses: list of ResponseItem (question_id, selected_choice, other_text)
    """
    session = await _get_session(db, session_id, user_id)

    if session.status != SessionStatus.MEDIA_UPLOADED:
        raise ValidationError("この操作は現在のセッション状態では実行できません")

    # Get all questions for this session
    result = await db.execute(
        select(ContextQuestion).where(ContextQuestion.session_id == session_id)
    )
    questions = list(result.scalars().all())

    if not questions:
        raise ValidationError("設問が見つかりません。メディアのアップロードを先に完了してください")

    # Validate all questions answered
    question_map = {q.id: q for q in questions}
    if len(responses) != len(questions):
        raise ValidationError(
            f"全{len(questions)}問に回答してください（{len(responses)}問の回答が送信されました）"
        )

    # Check for existing responses
    existing = await db.execute(
        select(ContextResponse).where(ContextResponse.session_id == session_id)
    )
    if list(existing.scalars().all()):
        raise ValidationError("すでに回答済みです")

    # Validate and save each response
    saved_responses = []
    for resp in responses:
        question = question_map.get(resp.question_id)
        if question is None:
            raise ValidationError(f"設問ID {resp.question_id} はこのセッションに存在しません")

        # Validate choice exists in question's choices
        valid_labels = [c["label"] for c in question.choices]
        if resp.selected_choice not in valid_labels:
            raise ValidationError(
                f"設問「{question.question_text}」に対して無効な選択肢です: {resp.selected_choice}"
            )

        # Validate other_text
        if resp.selected_choice == "X" and not resp.other_text:
            raise ValidationError(
                f"設問「{question.question_text}」で「その他」を選択した場合は記述が必要です"
            )
        if resp.selected_choice != "X" and resp.other_text:
            raise ValidationError(
                f"設問「{question.question_text}」で「その他」以外を選択した場合は記述不要です"
            )

        context_response = ContextResponse(
            question_id=resp.question_id,
            session_id=session_id,
            selected_choice=resp.selected_choice,
            other_text=resp.other_text if resp.selected_choice == "X" else None,
        )
        db.add(context_response)
        saved_responses.append(context_response)

    await db.flush()
    return saved_responses


async def submit_free_text(
    db: AsyncSession, session_id: str, user_id: str, content: str
) -> FreeTextInput:
    """Submit optional free text input."""
    session = await _get_session(db, session_id, user_id)

    if session.status != SessionStatus.MEDIA_UPLOADED:
        raise ValidationError("この操作は現在のセッション状態では実行できません")

    # Check all questions answered
    questions_result = await db.execute(
        select(ContextQuestion).where(ContextQuestion.session_id == session_id)
    )
    questions = list(questions_result.scalars().all())
    responses_result = await db.execute(
        select(ContextResponse).where(ContextResponse.session_id == session_id)
    )
    responses = list(responses_result.scalars().all())

    if len(responses) != len(questions):
        raise ValidationError("全設問に回答してから自由記述を入力してください")

    # Check for existing free text
    existing = await db.execute(
        select(FreeTextInput).where(FreeTextInput.session_id == session_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise ValidationError("自由記述は1セッションにつき1回のみ入力可能です")

    free_text = FreeTextInput(
        session_id=session_id,
        content=content,
    )
    db.add(free_text)
    await db.flush()
    return free_text


async def complete_questions(
    db: AsyncSession, session_id: str, user_id: str
) -> list[EmotionCandidate]:
    """Complete question phase and generate emotion candidates.

    Transitions status: media_uploaded → questions_answered
    """
    session = await _get_session(db, session_id, user_id)

    if session.status != SessionStatus.MEDIA_UPLOADED:
        raise ValidationError("この操作は現在のセッション状態では実行できません")

    # Validate all questions answered
    questions_result = await db.execute(
        select(ContextQuestion).where(
            ContextQuestion.session_id == session_id
        ).order_by(ContextQuestion.question_order)
    )
    questions = list(questions_result.scalars().all())

    responses_result = await db.execute(
        select(ContextResponse).where(ContextResponse.session_id == session_id)
    )
    responses = list(responses_result.scalars().all())

    if len(responses) != len(questions):
        raise ValidationError("全設問に回答してから完了してください")

    # Load analysis results
    media_result = await db.execute(
        select(MediaFile).where(MediaFile.session_id == session_id)
    )
    media_file = media_result.scalar_one_or_none()

    image_analysis = None
    music_analysis = None
    if media_file:
        if media_file.media_type == "image":
            r = await db.execute(
                select(ImageAnalysisResult).where(
                    ImageAnalysisResult.media_id == media_file.id
                )
            )
            image_analysis = r.scalar_one_or_none()
        else:
            r = await db.execute(
                select(MusicAnalysisResult).where(
                    MusicAnalysisResult.media_id == media_file.id
                )
            )
            music_analysis = r.scalar_one_or_none()

    # Load free text (optional)
    free_text_result = await db.execute(
        select(FreeTextInput).where(FreeTextInput.session_id == session_id)
    )
    free_text_record = free_text_result.scalar_one_or_none()
    free_text = free_text_record.content if free_text_record else None

    # Generate emotion candidates
    candidates = await generate_emotions(
        db=db,
        session_id=session_id,
        image_analysis=image_analysis,
        music_analysis=music_analysis,
        responses=responses,
        questions=questions,
        free_text=free_text,
    )

    # Update session status
    session.status = SessionStatus.QUESTIONS_ANSWERED
    await db.flush()

    return candidates


async def select_emotions(
    db: AsyncSession, session_id: str, user_id: str, candidate_ids: list[str]
) -> list[EmotionSelection]:
    """Select emotions from candidates.

    Transitions status: questions_answered → emotions_selected
    """
    session = await _get_session(db, session_id, user_id)

    if session.status != SessionStatus.QUESTIONS_ANSWERED:
        raise ValidationError("この操作は現在のセッション状態では実行できません")

    # Validate all candidate_ids belong to this session
    candidates_result = await db.execute(
        select(EmotionCandidate).where(EmotionCandidate.session_id == session_id)
    )
    valid_candidates = {c.id for c in candidates_result.scalars().all()}

    for cid in candidate_ids:
        if cid not in valid_candidates:
            raise ValidationError(f"感情候補ID {cid} はこのセッションに存在しません")

    # Check no existing selections
    existing = await db.execute(
        select(EmotionSelection).where(EmotionSelection.session_id == session_id)
    )
    if list(existing.scalars().all()):
        raise ValidationError("すでに感情を選択済みです")

    # Save selections
    selections = []
    for cid in candidate_ids:
        selection = EmotionSelection(
            candidate_id=cid,
            session_id=session_id,
        )
        db.add(selection)
        selections.append(selection)

    # Update session status
    session.status = SessionStatus.EMOTIONS_SELECTED
    await db.flush()

    return selections


async def get_questions(
    db: AsyncSession, session_id: str, user_id: str
) -> tuple[list[ContextQuestion], list[ContextResponse]]:
    """Get questions and their responses for a session."""
    await _get_session(db, session_id, user_id)

    questions_result = await db.execute(
        select(ContextQuestion)
        .where(ContextQuestion.session_id == session_id)
        .order_by(ContextQuestion.question_order)
    )
    questions = list(questions_result.scalars().all())

    responses_result = await db.execute(
        select(ContextResponse).where(ContextResponse.session_id == session_id)
    )
    responses = list(responses_result.scalars().all())

    return questions, responses


async def get_emotions(
    db: AsyncSession, session_id: str, user_id: str
) -> tuple[list[EmotionCandidate], list[EmotionSelection]]:
    """Get emotion candidates and selections for a session."""
    await _get_session(db, session_id, user_id)

    candidates_result = await db.execute(
        select(EmotionCandidate)
        .where(EmotionCandidate.session_id == session_id)
        .order_by(EmotionCandidate.candidate_order)
    )
    candidates = list(candidates_result.scalars().all())

    selections_result = await db.execute(
        select(EmotionSelection).where(EmotionSelection.session_id == session_id)
    )
    selections = list(selections_result.scalars().all())

    return candidates, selections
