import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.data.logic import create_session, delete_session, get_user_sessions
from app.data.models import GenerationSession, SessionStatus


@pytest.mark.asyncio
class TestCreateSession:
    async def test_create_session_success(self, db_session: AsyncSession):
        # First, create a user
        from app.auth.logic import register_user

        auth = await register_user(db_session, "session@test.com", "password123")
        await db_session.commit()

        session = await create_session(db_session, auth.user_id)
        assert session.user_id == auth.user_id
        assert session.status == SessionStatus.CREATED

    async def test_create_session_limit_one_active(self, db_session: AsyncSession):
        from app.auth.logic import register_user

        auth = await register_user(db_session, "limit@test.com", "password123")
        await db_session.commit()

        await create_session(db_session, auth.user_id)
        await db_session.commit()

        with pytest.raises(ConflictError):
            await create_session(db_session, auth.user_id)

    async def test_create_session_after_completed(self, db_session: AsyncSession):
        from app.auth.logic import register_user

        auth = await register_user(db_session, "complete@test.com", "password123")
        await db_session.commit()

        session = await create_session(db_session, auth.user_id)
        session.status = SessionStatus.COMPLETED
        await db_session.commit()

        # Should allow new session after completing the previous one
        new_session = await create_session(db_session, auth.user_id)
        assert new_session.status == SessionStatus.CREATED


@pytest.mark.asyncio
class TestDeleteSession:
    async def test_delete_session_success(self, db_session: AsyncSession):
        from app.auth.logic import register_user

        auth = await register_user(db_session, "del@test.com", "password123")
        await db_session.commit()

        session = await create_session(db_session, auth.user_id)
        await db_session.commit()

        await delete_session(db_session, session.id, auth.user_id)
        await db_session.commit()

        sessions, total = await get_user_sessions(db_session, auth.user_id)
        assert total == 0

    async def test_delete_session_not_found(self, db_session: AsyncSession):
        from app.auth.logic import register_user

        auth = await register_user(db_session, "notfound@test.com", "password123")
        await db_session.commit()

        with pytest.raises(NotFoundError):
            await delete_session(db_session, "nonexistent-id", auth.user_id)

    async def test_delete_session_wrong_owner(self, db_session: AsyncSession):
        from app.auth.logic import register_user

        auth1 = await register_user(db_session, "owner1@test.com", "password123")
        auth2 = await register_user(db_session, "owner2@test.com", "password123")
        await db_session.commit()

        session = await create_session(db_session, auth1.user_id)
        await db_session.commit()

        with pytest.raises(ForbiddenError):
            await delete_session(db_session, session.id, auth2.user_id)


@pytest.mark.asyncio
class TestGetUserSessions:
    async def test_get_sessions_empty(self, db_session: AsyncSession):
        from app.auth.logic import register_user

        auth = await register_user(db_session, "empty@test.com", "password123")
        await db_session.commit()

        sessions, total = await get_user_sessions(db_session, auth.user_id)
        assert total == 0
        assert sessions == []
