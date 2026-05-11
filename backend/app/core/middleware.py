from datetime import datetime, timezone

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError

security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Extract and validate JWT token, return current user ID."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise UnauthorizedError("Invalid token")

    exp = payload.get("exp")
    if exp is None or datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
        raise UnauthorizedError("Token expired")

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token")

    # Verify user still exists
    from app.auth.models import User

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("Invalid token")

    return user_id
