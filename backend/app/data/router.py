from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import MessageResponse
from app.core.database import get_db
from app.core.middleware import get_current_user_id
from app.data.logic import create_session, delete_session, get_user_sessions
from app.data.models import SessionListResponse, SessionResponse

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's generation sessions."""
    sessions, total = await get_user_sessions(db, user_id, page, per_page)
    return SessionListResponse(
        items=[
            SessionResponse(
                id=s.id,
                user_id=s.user_id,
                status=s.status.value,
                media_type=s.media_type,
                created_at=s.created_at,
                updated_at=s.updated_at,
                completed_at=s.completed_at,
            )
            for s in sessions
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def new_session(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new generation session."""
    session = await create_session(db, user_id)
    return SessionResponse(
        id=session.id,
        user_id=session.user_id,
        status=session.status.value,
        media_type=session.media_type,
        created_at=session.created_at,
        updated_at=session.updated_at,
        completed_at=session.completed_at,
    )


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def remove_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a generation session and all associated data."""
    await delete_session(db, session_id, user_id)
    return MessageResponse(message="セッションを削除しました")
