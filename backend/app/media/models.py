import uuid
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.auth.models import Base


class MediaFile(Base):
    __tablename__ = "media_files"

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
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    media_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ImageAnalysisResult(Base):
    __tablename__ = "image_analysis_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    media_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("media_files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    colors: Mapped[list] = mapped_column(JSON, nullable=False)
    composition: Mapped[str] = mapped_column(String(500), nullable=False)
    mood: Mapped[str] = mapped_column(String(200), nullable=False)
    subjects: Mapped[list] = mapped_column(JSON, nullable=False)
    atmosphere: Mapped[str] = mapped_column(String(500), nullable=False)
    texture: Mapped[str] = mapped_column(String(300), nullable=False)
    light_direction: Mapped[str] = mapped_column(String(200), nullable=False)
    emotional_impression: Mapped[str] = mapped_column(String(500), nullable=False)
    image_category: Mapped[str] = mapped_column(String(100), nullable=False)
    style_characteristics: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class MusicAnalysisResult(Base):
    __tablename__ = "music_analysis_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    media_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("media_files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    artist: Mapped[str | None] = mapped_column(String(255), nullable=True)
    album: Mapped[str | None] = mapped_column(String(255), nullable=True)
    genre: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    chord_progression: Mapped[str | None] = mapped_column(String(500), nullable=True)
    rhythm: Mapped[str] = mapped_column(String(200), nullable=False)
    tempo: Mapped[str] = mapped_column(String(100), nullable=False)
    mood: Mapped[str] = mapped_column(String(200), nullable=False)
    energy_level: Mapped[str] = mapped_column(String(100), nullable=False)
    emotional_impression: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_response: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


# --- Pydantic Schemas ---


class ImageAnalysisSchema(BaseModel):
    colors: list[str]
    composition: str
    mood: str
    subjects: list[str]
    atmosphere: str
    texture: str
    light_direction: str
    emotional_impression: str
    image_category: str
    style_characteristics: str


class MusicAnalysisSchema(BaseModel):
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    genre: str | None = None
    year: int | None = None
    duration_seconds: int | None = None
    bpm: int | None = None
    key: str | None = None
    chord_progression: str | None = None
    rhythm: str
    tempo: str
    mood: str
    energy_level: str
    emotional_impression: str


class MediaFileSchema(BaseModel):
    id: str
    session_id: str
    user_id: str
    media_type: str
    file_name: str
    file_size: int
    mime_type: str
    created_at: datetime


class MediaUploadResponse(BaseModel):
    media_file: MediaFileSchema
    image_analysis: ImageAnalysisSchema | None = None
    music_analysis: MusicAnalysisSchema | None = None


class MediaDetailResponse(BaseModel):
    media_file: MediaFileSchema
    image_analysis: ImageAnalysisSchema | None = None
    music_analysis: MusicAnalysisSchema | None = None
    presigned_url: str


class PresignedUrlResponse(BaseModel):
    presigned_url: str
    expires_in: int = 3600
