import pytest

from app.media.validators import (
    detect_media_type,
    validate_file_size,
    validate_mime_and_extension,
    validate_upload_file,
)


class TestDetectMediaType:
    def test_explicit_image(self):
        assert detect_media_type("image/jpeg", "image") == "image"

    def test_explicit_music(self):
        assert detect_media_type("audio/mpeg", "music") == "music"

    def test_auto_detect_image(self):
        assert detect_media_type("image/png") == "image"

    def test_auto_detect_music(self):
        assert detect_media_type("audio/mpeg") == "music"

    def test_invalid_explicit_type(self):
        with pytest.raises(Exception) as exc_info:
            detect_media_type("image/jpeg", "video")
        assert "image" in str(exc_info.value.detail) or "music" in str(exc_info.value.detail)

    def test_unknown_mime(self):
        with pytest.raises(Exception):
            detect_media_type("application/pdf")


class TestValidateMimeAndExtension:
    def test_valid_jpeg(self):
        validate_mime_and_extension("image/jpeg", "photo.jpg", "image")

    def test_valid_jpeg_extension(self):
        validate_mime_and_extension("image/jpeg", "photo.jpeg", "image")

    def test_valid_png(self):
        validate_mime_and_extension("image/png", "photo.png", "image")

    def test_valid_webp(self):
        validate_mime_and_extension("image/webp", "photo.webp", "image")

    def test_valid_gif(self):
        validate_mime_and_extension("image/gif", "anim.gif", "image")

    def test_valid_mp3(self):
        validate_mime_and_extension("audio/mpeg", "song.mp3", "music")

    def test_valid_wav(self):
        validate_mime_and_extension("audio/wav", "song.wav", "music")

    def test_valid_flac(self):
        validate_mime_and_extension("audio/flac", "song.flac", "music")

    def test_valid_aac(self):
        validate_mime_and_extension("audio/aac", "song.aac", "music")

    def test_valid_m4a(self):
        validate_mime_and_extension("audio/mp4", "song.m4a", "music")

    def test_invalid_mime_for_image(self):
        with pytest.raises(Exception):
            validate_mime_and_extension("audio/mpeg", "song.mp3", "image")

    def test_invalid_mime_for_music(self):
        with pytest.raises(Exception):
            validate_mime_and_extension("image/jpeg", "photo.jpg", "music")

    def test_mime_extension_mismatch(self):
        with pytest.raises(Exception) as exc_info:
            validate_mime_and_extension("image/jpeg", "photo.png", "image")
        assert "一致しません" in str(exc_info.value.detail)

    def test_case_insensitive_extension(self):
        validate_mime_and_extension("image/jpeg", "PHOTO.JPG", "image")


class TestValidateFileSize:
    def test_valid_image_size(self):
        validate_file_size(1024, "image")  # 1KB

    def test_valid_music_size(self):
        validate_file_size(1024 * 1024, "music")  # 1MB

    def test_empty_file(self):
        with pytest.raises(Exception) as exc_info:
            validate_file_size(0, "image")
        assert "空" in str(exc_info.value.detail)

    def test_image_too_large(self):
        with pytest.raises(Exception):
            validate_file_size(11 * 1024 * 1024, "image")  # 11MB

    def test_music_too_large(self):
        with pytest.raises(Exception):
            validate_file_size(51 * 1024 * 1024, "music")  # 51MB

    def test_image_at_limit(self):
        validate_file_size(10 * 1024 * 1024, "image")  # exactly 10MB

    def test_music_at_limit(self):
        validate_file_size(50 * 1024 * 1024, "music")  # exactly 50MB


class TestValidateUploadFile:
    def test_valid_jpeg_upload(self):
        validate_upload_file("photo.jpg", 5 * 1024 * 1024, "image/jpeg", "image")

    def test_valid_mp3_upload(self):
        validate_upload_file("song.mp3", 20 * 1024 * 1024, "audio/mpeg", "music")

    def test_invalid_mime_caught(self):
        with pytest.raises(Exception):
            validate_upload_file("doc.pdf", 1024, "application/pdf", "image")

    def test_oversized_caught(self):
        with pytest.raises(Exception):
            validate_upload_file("photo.jpg", 11 * 1024 * 1024, "image/jpeg", "image")
