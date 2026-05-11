from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.middleware import get_current_user_id
from app.media.logic import get_media_detail, get_presigned_url, upload_and_analyze
from app.media.models import (
    ImageAnalysisSchema,
    MediaDetailResponse,
    MediaFileSchema,
    MediaUploadResponse,
    MusicAnalysisSchema,
    PresignedUrlResponse,
)

router = APIRouter(prefix="/api/media", tags=["media"])


def _to_media_schema(media_file) -> MediaFileSchema:
    return MediaFileSchema(
        id=media_file.id,
        session_id=media_file.session_id,
        user_id=media_file.user_id,
        media_type=media_file.media_type,
        file_name=media_file.file_name,
        file_size=media_file.file_size,
        mime_type=media_file.mime_type,
        created_at=media_file.created_at,
    )


def _to_image_schema(analysis) -> ImageAnalysisSchema | None:
    if analysis is None:
        return None
    return ImageAnalysisSchema(
        colors=analysis.colors,
        composition=analysis.composition,
        mood=analysis.mood,
        subjects=analysis.subjects,
        atmosphere=analysis.atmosphere,
        texture=analysis.texture,
        light_direction=analysis.light_direction,
        emotional_impression=analysis.emotional_impression,
        image_category=analysis.image_category,
        style_characteristics=analysis.style_characteristics,
    )


def _to_music_schema(analysis) -> MusicAnalysisSchema | None:
    if analysis is None:
        return None
    return MusicAnalysisSchema(
        title=analysis.title,
        artist=analysis.artist,
        album=analysis.album,
        genre=analysis.genre,
        year=analysis.year,
        duration_seconds=analysis.duration_seconds,
        bpm=analysis.bpm,
        key=analysis.key,
        chord_progression=analysis.chord_progression,
        rhythm=analysis.rhythm,
        tempo=analysis.tempo,
        mood=analysis.mood,
        energy_level=analysis.energy_level,
        emotional_impression=analysis.emotional_impression,
    )


@router.post("/upload", response_model=MediaUploadResponse, status_code=201)
async def upload_media(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    media_type: str | None = Form(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Upload a media file and run AI analysis (synchronous)."""
    file_data = await file.read()
    file_name = file.filename or "unknown"
    mime_type = file.content_type or "application/octet-stream"

    media_file, image_analysis, music_analysis = await upload_and_analyze(
        db=db,
        session_id=session_id,
        user_id=user_id,
        file_data=file_data,
        file_name=file_name,
        mime_type=mime_type,
        media_type_param=media_type,
    )

    return MediaUploadResponse(
        media_file=_to_media_schema(media_file),
        image_analysis=_to_image_schema(image_analysis),
        music_analysis=_to_music_schema(music_analysis),
    )


@router.get("/{media_id}", response_model=MediaDetailResponse)
async def get_media(
    media_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get media file details with analysis result and presigned URL."""
    media_file, image_analysis, music_analysis = await get_media_detail(db, media_id, user_id)
    url = await get_presigned_url(db, media_id, user_id)

    return MediaDetailResponse(
        media_file=_to_media_schema(media_file),
        image_analysis=_to_image_schema(image_analysis),
        music_analysis=_to_music_schema(music_analysis),
        presigned_url=url,
    )


@router.get("/{media_id}/presigned-url", response_model=PresignedUrlResponse)
async def get_media_presigned_url(
    media_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate a presigned URL for downloading the media file."""
    url = await get_presigned_url(db, media_id, user_id)
    return PresignedUrlResponse(presigned_url=url)
