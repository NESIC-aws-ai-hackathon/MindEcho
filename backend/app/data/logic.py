import logging

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import s3_client
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.data.models import GenerationSession, SessionStatus

logger = logging.getLogger(__name__)


async def get_user_sessions(
    db: AsyncSession, user_id: str, page: int = 1, per_page: int = 20
) -> tuple[list[GenerationSession], int]:
    """Get paginated sessions for a user."""
    # Count total
    count_result = await db.execute(
        select(func.count()).where(GenerationSession.user_id == user_id)
    )
    total = count_result.scalar() or 0

    # Fetch page
    offset = (page - 1) * per_page
    result = await db.execute(
        select(GenerationSession)
        .where(GenerationSession.user_id == user_id)
        .order_by(GenerationSession.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    sessions = list(result.scalars().all())
    return sessions, total


async def create_session(db: AsyncSession, user_id: str) -> GenerationSession:
    """Create a new generation session (max 1 active per user)."""
    # Check active session limit (BR-SESSION-01)
    result = await db.execute(
        select(func.count()).where(
            GenerationSession.user_id == user_id,
            GenerationSession.status != SessionStatus.COMPLETED,
        )
    )
    active_count = result.scalar() or 0
    if active_count >= 1:
        raise ConflictError(
            "アクティブなセッションが存在します。完了してから新しいセッションを開始してください。"
        )

    session = GenerationSession(user_id=user_id)
    db.add(session)
    await db.flush()
    return session


async def delete_session(db: AsyncSession, session_id: str, user_id: str) -> None:
    """Delete a single session and its associated S3 files."""
    result = await db.execute(
        select(GenerationSession).where(GenerationSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise NotFoundError("セッションが見つかりません")
    if session.user_id != user_id:
        raise ForbiddenError("このセッションを削除する権限がありません")

    # Delete S3 files associated with this session
    await _delete_session_s3_files(db, session_id)

    # Delete session (CASCADE will delete child records)
    await db.delete(session)


async def delete_all_user_data(db: AsyncSession, user_id: str) -> None:
    """Delete all sessions and S3 files for a user."""
    result = await db.execute(
        select(GenerationSession).where(GenerationSession.user_id == user_id)
    )
    sessions = result.scalars().all()

    # Collect and delete all S3 files
    for session in sessions:
        try:
            await _delete_session_s3_files(db, session.id)
        except Exception as e:
            logger.warning(f"Failed to delete S3 files for session {session.id}: {e}")

    # Delete all sessions (CASCADE handles child records)
    await db.execute(
        delete(GenerationSession).where(GenerationSession.user_id == user_id)
    )


async def _delete_session_s3_files(db: AsyncSession, session_id: str) -> None:
    """Delete S3 files associated with a session."""
    # Query media_files table for s3_keys (will exist after Unit 1 is implemented)
    try:
        from sqlalchemy import text

        result = await db.execute(
            text("SELECT s3_key FROM media_files WHERE session_id = :sid"),
            {"sid": session_id},
        )
        s3_keys = [row[0] for row in result.fetchall()]
        if s3_keys:
            await s3_client.delete_files(s3_keys)
    except Exception as e:
        # media_files table may not exist yet (Unit 1 not deployed)
        logger.debug(f"S3 cleanup skipped for session {session_id}: {e}")
