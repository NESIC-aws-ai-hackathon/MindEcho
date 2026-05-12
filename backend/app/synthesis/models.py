import enum
import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, field_validator
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import Base


class OutputFormat(str, enum.Enum):
    SNS = "sns"
    DIARY = "diary"
    REVIEW = "review"


OUTPUT_FORMAT_INFO = [
    {
        "id": "sns",
        "name": "SNS投稿",
        "description": "カジュアルな短文。ハッシュタグ付き。",
        "min_chars": 140,
        "max_chars": 280,
        "is_default": True,
    },
    {
        "id": "diary",
        "name": "日記・メモ",
        "description": "内省的で個人的な文章。",
        "min_chars": 300,
        "max_chars": 500,
        "is_default": False,
    },
    {
        "id": "review",
        "name": "レビュー記事",
        "description": "構造的で分析的な長文。",
        "min_chars": 500,
        "max_chars": 1000,
        "is_default": False,
    },
]


class GeneratedText(Base):
    __tablename__ = "generated_texts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    output_format: Mapped[str] = mapped_column(String(20), nullable=False)
    generated_content: Mapped[str] = mapped_column(Text, nullable=False)
    generation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# --- Pydantic Schemas ---

VALID_FORMATS = {"sns", "diary", "review"}


class GenerateRequest(BaseModel):
    session_id: str
    output_format: str

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        if v not in VALID_FORMATS:
            raise ValueError(f"出力形式は {', '.join(VALID_FORMATS)} のいずれかを指定してください")
        return v


class GeneratedTextSchema(BaseModel):
    session_id: str
    output_format: str
    generated_content: str
    generation_count: int
    created_at: datetime
    updated_at: datetime


class FormatInfo(BaseModel):
    id: str
    name: str
    description: str
    min_chars: int
    max_chars: int
    is_default: bool


class FormatsResponse(BaseModel):
    formats: list[FormatInfo]
