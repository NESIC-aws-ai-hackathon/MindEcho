import enum
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import Base


class SessionStatus(str, enum.Enum):
    CREATED = "created"
    MEDIA_UPLOADED = "media_uploaded"
    QUESTIONS_ANSWERED = "questions_answered"
    EMOTIONS_SELECTED = "emotions_selected"
    GENERATED = "generated"
    COMPLETED = "completed"


class GenerationSession(Base):
    __tablename__ = "generation_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), nullable=False, default=SessionStatus.CREATED
    )
    media_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# --- Pydantic Schemas ---


class SessionResponse(BaseModel):
    id: str
    user_id: str
    status: str
    media_type: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    total: int
    page: int
    per_page: int
