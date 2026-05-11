import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import s3_client
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.data.models import GenerationSession, SessionStatus
from app.media.image_analyzer import analyze_image
from app.media.models import ImageAnalysisResult, MediaFile, MusicAnalysisResult
from app.media.music_analyzer import analyze_music
from app.media.validators import detect_media_type, validate_upload_file

logger = logging.getLogger(__name__)


def _generate_s3_key(media_type: str, file_name: str) -> str:
    """Generate S3 key: {media_type}/{year}/{month}/{uuid}.{ext}"""
    now = datetime.now(timezone.utc)
    dot_index = file_name.rfind(".")
    ext = file_name[dot_index + 1:].lower() if dot_index != -1 else "bin"
    return f"{media_type}/{now.year}/{now.month:02d}/{uuid.uuid4()}.{ext}"


async def upload_and_analyze(
    db: AsyncSession,
    session_id: str,
    user_id: str,
    file_data: bytes,
    file_name: str,
    mime_type: str,
    media_type_param: str | None = None,
) -> tuple[MediaFile, ImageAnalysisResult | None, MusicAnalysisResult | None]:
    """Upload media file to S3, run AI analysis, and save results.

    Returns:
        Tuple of (media_file, image_analysis_or_none, music_analysis_or_none)
    """
    # 1. Detect media type
    media_type = detect_media_type(mime_type, media_type_param)

    # 2. Validate file
    validate_upload_file(file_name, len(file_data), mime_type, media_type)

    # 3. Validate session
    result = await db.execute(
        select(GenerationSession).where(GenerationSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if session is None:
        raise NotFoundError("セッションが見つかりません")
    if session.user_id != user_id:
        raise ForbiddenError("このセッションにメディアをアップロードする権限がありません")
    if session.status != SessionStatus.CREATED:
        raise ValidationError("このセッションにはすでにメディアがアップロードされています")

    # Check for existing media (1 media per session)
    existing = await db.execute(
        select(MediaFile).where(MediaFile.session_id == session_id)
    )
    if existing.scalar_one_or_none() is not None:
        raise ValidationError("このセッションにはすでにメディアがアップロードされています")

    # 4. Upload to S3
    s3_key = _generate_s3_key(media_type, file_name)
    try:
        await s3_client.upload_file(s3_key, file_data, mime_type)
    except Exception:
        logger.error("S3 upload failed for %s", file_name, exc_info=True)
        raise ValidationError("ファイルのアップロードに失敗しました")

    # 5. Save MediaFile record
    media_file = MediaFile(
        session_id=session_id,
        user_id=user_id,
        media_type=media_type,
        file_name=file_name,
        file_size=len(file_data),
        mime_type=mime_type,
        s3_key=s3_key,
    )
    db.add(media_file)
    await db.flush()

    # 6. Run AI analysis
    image_analysis = None
    music_analysis = None

    try:
        if media_type == "image":
            analysis_data, raw_response = await analyze_image(file_data, mime_type)
            image_analysis = ImageAnalysisResult(
                media_id=media_file.id,
                colors=analysis_data["colors"],
                composition=analysis_data["composition"],
                mood=analysis_data["mood"],
                subjects=analysis_data["subjects"],
                atmosphere=analysis_data["atmosphere"],
                texture=analysis_data["texture"],
                light_direction=analysis_data["light_direction"],
                emotional_impression=analysis_data["emotional_impression"],
                image_category=analysis_data["image_category"],
                style_characteristics=analysis_data["style_characteristics"],
                raw_response=raw_response,
            )
            db.add(image_analysis)
        else:
            analysis_data, raw_response = await analyze_music(file_data, file_name)
            music_analysis = MusicAnalysisResult(
                media_id=media_file.id,
                title=analysis_data.get("title"),
                artist=analysis_data.get("artist"),
                album=analysis_data.get("album"),
                genre=analysis_data.get("genre"),
                year=analysis_data.get("year"),
                duration_seconds=analysis_data.get("duration_seconds"),
                bpm=analysis_data.get("bpm"),
                key=analysis_data.get("key"),
                chord_progression=analysis_data.get("chord_progression"),
                rhythm=analysis_data["rhythm"],
                tempo=analysis_data["tempo"],
                mood=analysis_data["mood"],
                energy_level=analysis_data["energy_level"],
                emotional_impression=analysis_data["emotional_impression"],
                raw_response=raw_response,
            )
            db.add(music_analysis)

    except Exception:
        # Rollback: delete S3 file on analysis failure
        logger.error("Analysis failed, rolling back S3 upload for %s", s3_key, exc_info=True)
        try:
            await s3_client.delete_file(s3_key)
        except Exception:
            logger.warning("Failed to rollback S3 file %s", s3_key, exc_info=True)
        raise ValidationError("メディアの解析に失敗しました。再度お試しください。")

    # 7. Update session status
    session.status = SessionStatus.MEDIA_UPLOADED
    session.media_type = media_type

    await db.flush()

    # 8. Generate context questions (non-blocking: failure doesn't fail upload)
    try:
        from app.cognitive.question_generator import generate_questions
        await generate_questions(db, session_id, media_file, image_analysis, music_analysis)
    except Exception:
        logger.warning(
            "Question generation failed for session %s, will use fallback later",
            session_id,
            exc_info=True,
        )

    return media_file, image_analysis, music_analysis


async def get_media_detail(
    db: AsyncSession, media_id: str, user_id: str
) -> tuple[MediaFile, ImageAnalysisResult | None, MusicAnalysisResult | None]:
    """Get media file with its analysis result."""
    result = await db.execute(
        select(MediaFile).where(MediaFile.id == media_id)
    )
    media_file = result.scalar_one_or_none()

    if media_file is None:
        raise NotFoundError("メディアファイルが見つかりません")
    if media_file.user_id != user_id:
        raise ForbiddenError("このメディアファイルへのアクセス権限がありません")

    image_analysis = None
    music_analysis = None

    if media_file.media_type == "image":
        r = await db.execute(
            select(ImageAnalysisResult).where(ImageAnalysisResult.media_id == media_id)
        )
        image_analysis = r.scalar_one_or_none()
    else:
        r = await db.execute(
            select(MusicAnalysisResult).where(MusicAnalysisResult.media_id == media_id)
        )
        music_analysis = r.scalar_one_or_none()

    return media_file, image_analysis, music_analysis


async def get_presigned_url(db: AsyncSession, media_id: str, user_id: str) -> str:
    """Generate a presigned URL for a media file."""
    result = await db.execute(
        select(MediaFile).where(MediaFile.id == media_id)
    )
    media_file = result.scalar_one_or_none()

    if media_file is None:
        raise NotFoundError("メディアファイルが見つかりません")
    if media_file.user_id != user_id:
        raise ForbiddenError("このメディアファイルへのアクセス権限がありません")

    return s3_client.generate_presigned_url(media_file.s3_key)
