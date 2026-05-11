import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, field_validator
from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import Base


class ContextQuestion(Base):
    __tablename__ = "context_questions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_order: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(String(500), nullable=False)
    choices: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ContextResponse(Base):
    __tablename__ = "context_responses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    question_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("context_questions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    selected_choice: Mapped[str] = mapped_column(String(10), nullable=False)
    other_text: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class FreeTextInput(Base):
    __tablename__ = "free_text_inputs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    content: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class EmotionCandidate(Base):
    __tablename__ = "emotion_candidates"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_order: Mapped[int] = mapped_column(Integer, nullable=False)
    emotion_label: Mapped[str] = mapped_column(String(100), nullable=False)
    emotion_description: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class EmotionSelection(Base):
    __tablename__ = "emotion_selections"
    __table_args__ = (
        UniqueConstraint("candidate_id", "session_id", name="uq_emotion_selection"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("emotion_candidates.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


# --- Pydantic Schemas ---


class ChoiceSchema(BaseModel):
    label: str
    text: str


class ContextQuestionSchema(BaseModel):
    id: str
    question_order: int
    question_text: str
    choices: list[ChoiceSchema]
    selected_choice: str | None = None
    other_text: str | None = None


class ResponseItem(BaseModel):
    question_id: str
    selected_choice: str
    other_text: str | None = None

    @field_validator("other_text")
    @classmethod
    def validate_other_text(cls, v: str | None, info) -> str | None:
        if v is not None and len(v) > 200:
            raise ValueError("「その他」の記述は200文字以内で入力してください")
        return v


class SubmitResponsesRequest(BaseModel):
    session_id: str
    responses: list[ResponseItem]


class FreeTextRequest(BaseModel):
    session_id: str
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("自由記述を入力してください")
        if len(v) > 500:
            raise ValueError("自由記述は500文字以内で入力してください")
        return v


class CompleteQuestionsRequest(BaseModel):
    session_id: str


class SelectEmotionsRequest(BaseModel):
    session_id: str
    candidate_ids: list[str]

    @field_validator("candidate_ids")
    @classmethod
    def validate_candidate_ids(cls, v: list[str]) -> list[str]:
        if len(v) < 1:
            raise ValueError("少なくとも1つの感情を選択してください")
        if len(v) != len(set(v)):
            raise ValueError("同じ感情を重複して選択することはできません")
        return v


class EmotionCandidateSchema(BaseModel):
    id: str
    candidate_order: int
    emotion_label: str
    emotion_description: str
    is_selected: bool = False


class QuestionsResponse(BaseModel):
    session_id: str
    questions: list[ContextQuestionSchema]


class EmotionsResponse(BaseModel):
    session_id: str
    candidates: list[EmotionCandidateSchema]
