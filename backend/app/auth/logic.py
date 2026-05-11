import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthResponse, User
from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    """Generate a JWT access token with 24-hour expiry."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def register_user(db: AsyncSession, email: str, password: str) -> AuthResponse:
    """Register a new user. Returns AuthResponse with token."""
    # Check for existing email
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        raise ConflictError("このメールアドレスは既に登録されています")

    # Create user
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    await db.flush()

    # Generate token
    token = create_access_token(user.id)
    return AuthResponse(user_id=user.id, access_token=token)


async def authenticate_user(db: AsyncSession, email: str, password: str) -> AuthResponse:
    """Authenticate a user by email and password. Returns AuthResponse with token."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Unified error message for security (BR-AUTH-05)
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError()

    token = create_access_token(user.id)
    return AuthResponse(user_id=user.id, access_token=token)


async def delete_account(db: AsyncSession, user_id: str) -> None:
    """Delete a user account and all associated data."""
    from app.data.logic import delete_all_user_data

    # Delete all user data (sessions, S3 files, etc.)
    await delete_all_user_data(db, user_id)

    # Delete user record
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        await db.delete(user)
