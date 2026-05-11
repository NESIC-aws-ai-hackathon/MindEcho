from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.logic import (
    complete_questions,
    get_emotions,
    get_questions,
    select_emotions,
    submit_free_text,
    submit_responses,
)
from app.cognitive.models import (
    CompleteQuestionsRequest,
    ContextQuestionSchema,
    EmotionCandidateSchema,
    EmotionsResponse,
    FreeTextRequest,
    QuestionsResponse,
    SelectEmotionsRequest,
    SubmitResponsesRequest,
)
from app.core.database import get_db
from app.core.middleware import get_current_user_id

router = APIRouter(prefix="/api/cognitive", tags=["cognitive"])


@router.post("/responses", status_code=status.HTTP_201_CREATED)
async def post_responses(
    request: SubmitResponsesRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Submit responses to all context questions."""
    await submit_responses(db, request.session_id, user_id, request.responses)
    await db.commit()
    return {"message": "回答を受け付けました"}


@router.post("/free-text", status_code=status.HTTP_201_CREATED)
async def post_free_text(
    request: FreeTextRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Submit optional free text input."""
    await submit_free_text(db, request.session_id, user_id, request.content)
    await db.commit()
    return {"message": "自由記述を受け付けました"}


@router.post("/complete-questions", status_code=status.HTTP_201_CREATED)
async def post_complete_questions(
    request: CompleteQuestionsRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Complete question phase and generate emotion candidates."""
    candidates = await complete_questions(db, request.session_id, user_id)
    await db.commit()
    return EmotionsResponse(
        session_id=request.session_id,
        candidates=[
            EmotionCandidateSchema(
                id=c.id,
                candidate_order=c.candidate_order,
                emotion_label=c.emotion_label,
                emotion_description=c.emotion_description,
                is_selected=False,
            )
            for c in candidates
        ],
    )


@router.post("/emotions", status_code=status.HTTP_201_CREATED)
async def post_emotions(
    request: SelectEmotionsRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Select emotions from candidates."""
    await select_emotions(db, request.session_id, user_id, request.candidate_ids)
    await db.commit()
    return {"message": "感情の選択を受け付けました"}


@router.get("/questions/{session_id}", response_model=QuestionsResponse)
async def get_session_questions(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get context questions and responses for a session."""
    questions, responses = await get_questions(db, session_id, user_id)
    response_map = {r.question_id: r for r in responses}

    return QuestionsResponse(
        session_id=session_id,
        questions=[
            ContextQuestionSchema(
                id=q.id,
                question_order=q.question_order,
                question_text=q.question_text,
                choices=q.choices,
                selected_choice=response_map[q.id].selected_choice if q.id in response_map else None,
                other_text=response_map[q.id].other_text if q.id in response_map else None,
            )
            for q in questions
        ],
    )


@router.get("/emotions/{session_id}", response_model=EmotionsResponse)
async def get_session_emotions(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get emotion candidates and selections for a session."""
    candidates, selections = await get_emotions(db, session_id, user_id)
    selected_ids = {s.candidate_id for s in selections}

    return EmotionsResponse(
        session_id=session_id,
        candidates=[
            EmotionCandidateSchema(
                id=c.id,
                candidate_order=c.candidate_order,
                emotion_label=c.emotion_label,
                emotion_description=c.emotion_description,
                is_selected=c.id in selected_ids,
            )
            for c in candidates
        ],
    )
