from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.logic import authenticate_user, delete_account, register_user
from app.auth.models import AuthResponse, LoginRequest, MessageResponse, RegisterRequest
from app.core.database import get_db
from app.core.middleware import get_current_user_id

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    return await register_user(db, request.email, request.password)


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and receive an access token."""
    return await authenticate_user(db, request.email, request.password)


@router.delete("/account", response_model=MessageResponse)
async def delete_my_account(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete the current user's account and all associated data."""
    await delete_account(db, user_id)
    return MessageResponse(message="アカウントを削除しました")
