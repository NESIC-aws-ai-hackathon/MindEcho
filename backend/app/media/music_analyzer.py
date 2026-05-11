import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.core.bedrock_client import invoke_model

logger = logging.getLogger(__name__)


# --- Metadata Extraction ---


@dataclass
class MusicMetadata:
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    genre: str | None = None
    year: int | None = None
    duration_seconds: int | None = None
    file_name: str = ""


def extract_metadata(file_data: bytes, file_name: str) -> MusicMetadata:
    """Extract metadata from audio file using mutagen."""
    try:
        import io

        import mutagen

        audio = mutagen.File(io.BytesIO(file_data))
        if audio is None:
            return MusicMetadata(file_name=file_name)

        tags = audio.tags or {}
        metadata = MusicMetadata(file_name=file_name)

        # ID3 tags (MP3)
        if hasattr(audio, "tags") and audio.tags:
            # Try common tag keys across formats
            for key_map in [
                # ID3
                {"title": "TIT2", "artist": "TPE1", "album": "TALB", "genre": "TCON", "year": "TDRC"},
                # Vorbis / FLAC
                {"title": "title", "artist": "artist", "album": "album", "genre": "genre", "year": "date"},
                # MP4/AAC
                {"title": "\xa9nam", "artist": "\xa9ART", "album": "\xa9alb", "genre": "\xa9gen", "year": "\xa9day"},
            ]:
                for attr, tag_key in key_map.items():
                    if tag_key in tags and not getattr(metadata, attr):
                        val = tags[tag_key]
                        if isinstance(val, list):
                            val = str(val[0]) if val else None
                        else:
                            val = str(val)
                        if val:
                            if attr == "year":
                                try:
                                    metadata.year = int(str(val)[:4])
                                except (ValueError, IndexError):
                                    pass
                            else:
                                setattr(metadata, attr, val)

        # Duration
        if hasattr(audio, "info") and audio.info:
            if hasattr(audio.info, "length") and audio.info.length:
                metadata.duration_seconds = int(audio.info.length)

        return metadata

    except Exception:
        logger.warning("Failed to extract metadata from %s", file_name, exc_info=True)
        return MusicMetadata(file_name=file_name)


def _title_from_filename(file_name: str) -> str:
    """Derive a title from a file name."""
    name = os.path.splitext(file_name)[0]
    return name.replace("_", " ").replace("-", " ").strip()


# --- Provider Pattern ---


@runtime_checkable
class MusicAnalysisProvider(Protocol):
    """Protocol for music analysis providers.

    Each provider returns a dict with the analysis fields it can provide.
    Fields not returned will be filled by other providers or defaults.
    """

    async def analyze(self, metadata: MusicMetadata) -> dict:
        """Analyze music and return a dict of analysis fields."""
        ...


class BedrockMusicProvider:
    """Default provider that uses AWS Bedrock for all analysis fields."""

    PROMPT_TEMPLATE = """あなたは音楽評論の専門家です。以下の楽曲メタデータから、
楽曲の印象を分析し、指定されたJSON形式で結果を返してください。

楽曲情報:
- タイトル: {title}
- アーティスト: {artist}
- アルバム: {album}
- ジャンル: {genre}
- リリース年: {year}
- 再生時間: {duration}秒

分析項目:
1. bpm: BPM（テンポの数値）を推定。不明な場合はnull（例: 120, 80, 140）
2. key: 楽曲のキーを推定。不明な場合はnull（例: "C major", "A minor", "F# minor"）
3. chord_progression: 主要なコード進行パターンを推定。不明な場合はnull（例: "I-V-vi-IV", "i-VI-III-VII"）
4. rhythm: リズムの特徴を推定（例: 「軽快な4拍子」「ゆったりとした3拍子」）
5. tempo: テンポの印象（例: 「アップテンポ」「ミドルテンポ」「スロー」）
6. mood: 楽曲のムード（例: 「哀愁」「高揚感」「癒し」）
7. energy_level: エネルギーレベル（例: 「高い」「中程度」「低い」）
8. emotional_impression: この楽曲が聴者に与える感情的印象を1〜2文で

出力形式（必ずこのJSON形式で）:
{{
  "bpm": 120,
  "key": "キー（不明時はnull）",
  "chord_progression": "コード進行（不明時はnull）",
  "rhythm": "リズムの特徴",
  "tempo": "テンポの印象",
  "mood": "ムード",
  "energy_level": "エネルギーレベル",
  "emotional_impression": "感情的印象の記述"
}}"""

    async def analyze(self, metadata: MusicMetadata) -> dict:
        title = metadata.title or _title_from_filename(metadata.file_name)
        prompt = self.PROMPT_TEMPLATE.format(
            title=title,
            artist=metadata.artist or "不明",
            album=metadata.album or "不明",
            genre=metadata.genre or "不明",
            year=metadata.year or "不明",
            duration=metadata.duration_seconds or "不明",
        )

        raw_response = await invoke_model(prompt)
        parsed = _extract_json(raw_response)

        result: dict = {"raw_response": raw_response}
        if parsed:
            for field in BEDROCK_FIELDS:
                if field in parsed:
                    result[field] = parsed[field]

        return result


BEDROCK_FIELDS = [
    "bpm", "key", "chord_progression",
    "rhythm", "tempo", "mood", "energy_level", "emotional_impression",
]

DEFAULT_VALUES = {
    "rhythm": "解析不可",
    "tempo": "解析不可",
    "mood": "解析不可",
    "energy_level": "解析不可",
    "emotional_impression": "解析不可",
}


def _extract_json(text: str) -> dict | None:
    """Extract JSON from text, handling ```json blocks."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


async def analyze_music(
    file_data: bytes,
    file_name: str,
    providers: list[MusicAnalysisProvider] | None = None,
) -> tuple[dict, str]:
    """Analyze music using metadata extraction and configurable providers.

    Args:
        file_data: Raw audio file bytes
        file_name: Original file name
        providers: List of analysis providers. If None, uses BedrockMusicProvider only.
                  When multiple providers return the same field, later providers win (override).

    Returns:
        Tuple of (analysis_dict, raw_response)
    """
    metadata = extract_metadata(file_data, file_name)

    if providers is None:
        providers = [BedrockMusicProvider()]

    # Collect results from all providers, later providers override earlier ones
    merged: dict = {}
    raw_response = ""

    for provider in providers:
        try:
            provider_result = await provider.analyze(metadata)
            if "raw_response" in provider_result:
                raw_response = provider_result.pop("raw_response")
            merged.update(provider_result)
        except Exception:
            logger.warning(
                "Provider %s failed for %s",
                type(provider).__name__,
                file_name,
                exc_info=True,
            )

    # Apply defaults for required fields
    for field, default in DEFAULT_VALUES.items():
        if field not in merged or not merged[field]:
            merged[field] = default

    # Build final result with metadata
    result = {
        "title": metadata.title,
        "artist": metadata.artist,
        "album": metadata.album,
        "genre": metadata.genre,
        "year": metadata.year,
        "duration_seconds": metadata.duration_seconds,
        "bpm": merged.get("bpm"),
        "key": merged.get("key"),
        "chord_progression": merged.get("chord_progression"),
        "rhythm": merged["rhythm"],
        "tempo": merged["tempo"],
        "mood": merged["mood"],
        "energy_level": merged["energy_level"],
        "emotional_impression": merged["emotional_impression"],
    }

    return result, raw_response
