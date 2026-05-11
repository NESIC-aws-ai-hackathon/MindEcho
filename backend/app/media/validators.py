from app.core.exceptions import ValidationError

# BR-MEDIA-01: 画像ファイル許可形式
ALLOWED_IMAGE_TYPES: dict[str, list[str]] = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/webp": [".webp"],
    "image/gif": [".gif"],
}

# BR-MEDIA-02: 音楽ファイル許可形式
ALLOWED_MUSIC_TYPES: dict[str, list[str]] = {
    "audio/mpeg": [".mp3"],
    "audio/wav": [".wav"],
    "audio/x-wav": [".wav"],
    "audio/flac": [".flac"],
    "audio/aac": [".aac"],
    "audio/mp4": [".m4a"],
}

# BR-MEDIA-04: ファイルサイズ制限
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_MUSIC_SIZE = 50 * 1024 * 1024  # 50MB


def _get_extension(file_name: str) -> str:
    """Extract file extension (lowercase, with dot)."""
    dot_index = file_name.rfind(".")
    if dot_index == -1:
        return ""
    return file_name[dot_index:].lower()


def detect_media_type(mime_type: str, media_type: str | None = None) -> str:
    """Detect media type from MIME type or explicit parameter.

    BR-MEDIA-06: 自動判定ロジック
    BR-MEDIA-07: media_typeパラメータバリデーション
    """
    if media_type is not None:
        if media_type not in ("image", "music"):
            raise ValidationError("メディア種別は 'image' または 'music' を指定してください")
        return media_type

    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("audio/"):
        return "music"

    raise ValidationError("メディア種別を判定できません")


def validate_mime_and_extension(mime_type: str, file_name: str, media_type: str) -> None:
    """Validate MIME type and extension consistency.

    BR-MEDIA-01, BR-MEDIA-02: 許可形式チェック
    BR-MEDIA-03: MIMEタイプと拡張子の整合性チェック
    """
    ext = _get_extension(file_name)
    allowed = ALLOWED_IMAGE_TYPES if media_type == "image" else ALLOWED_MUSIC_TYPES

    if mime_type not in allowed:
        raise ValidationError(f"許可されていないファイル形式です: {mime_type}")

    if ext not in allowed[mime_type]:
        raise ValidationError(
            f"ファイル形式が一致しません: MIMEタイプ '{mime_type}' と拡張子 '{ext}'"
        )


def validate_file_size(file_size: int, media_type: str) -> None:
    """Validate file size.

    BR-MEDIA-04: ファイルサイズ制限
    BR-MEDIA-05: 空ファイル拒否
    """
    if file_size == 0:
        raise ValidationError("空のファイルはアップロードできません")

    max_size = MAX_IMAGE_SIZE if media_type == "image" else MAX_MUSIC_SIZE
    if file_size > max_size:
        max_mb = max_size // (1024 * 1024)
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"ファイルサイズが上限（{max_mb}MB）を超えています",
                    "details": [],
                }
            },
        )


def validate_upload_file(file_name: str, file_size: int, mime_type: str, media_type: str) -> None:
    """Run all file validations."""
    validate_mime_and_extension(mime_type, file_name, media_type)
    validate_file_size(file_size, media_type)
