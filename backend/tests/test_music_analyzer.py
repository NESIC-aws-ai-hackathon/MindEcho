import json
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.media.music_analyzer import (
    BedrockMusicProvider,
    MusicAnalysisProvider,
    MusicMetadata,
    _extract_json,
    _title_from_filename,
    analyze_music,
    extract_metadata,
)


class TestExtractJson:
    def test_json_code_block(self):
        text = '```json\n{"rhythm": "4拍子"}\n```'
        result = _extract_json(text)
        assert result == {"rhythm": "4拍子"}

    def test_plain_json(self):
        text = '{"mood": "calm"}'
        result = _extract_json(text)
        assert result == {"mood": "calm"}

    def test_invalid_json(self):
        assert _extract_json("not json") is None


class TestTitleFromFilename:
    def test_simple(self):
        assert _title_from_filename("my_song.mp3") == "my song"

    def test_with_dashes(self):
        assert _title_from_filename("my-song.mp3") == "my song"

    def test_no_extension(self):
        assert _title_from_filename("mysong") == "mysong"


class TestExtractMetadata:
    def test_empty_data_returns_defaults(self):
        metadata = extract_metadata(b"not audio", "test.mp3")
        assert metadata.file_name == "test.mp3"
        assert metadata.title is None

    def test_preserves_filename(self):
        metadata = extract_metadata(b"", "my_song.flac")
        assert metadata.file_name == "my_song.flac"


class TestBedrockMusicProvider:
    @pytest.mark.asyncio
    async def test_analyze_parses_response(self):
        response_data = {
            "bpm": 120,
            "key": "C major",
            "chord_progression": "I-V-vi-IV",
            "rhythm": "軽快な4拍子",
            "tempo": "アップテンポ",
            "mood": "高揚感",
            "energy_level": "高い",
            "emotional_impression": "活力に溢れる楽曲",
        }
        raw = json.dumps(response_data, ensure_ascii=False)

        with patch("app.media.music_analyzer.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = raw
            provider = BedrockMusicProvider()
            metadata = MusicMetadata(title="Test Song", artist="Artist", file_name="test.mp3")
            result = await provider.analyze(metadata)

        assert result["bpm"] == 120
        assert result["key"] == "C major"
        assert result["chord_progression"] == "I-V-vi-IV"
        assert result["rhythm"] == "軽快な4拍子"
        assert "raw_response" in result

    @pytest.mark.asyncio
    async def test_analyze_with_null_fields(self):
        response_data = {
            "bpm": None,
            "key": None,
            "chord_progression": None,
            "rhythm": "不明なリズム",
            "tempo": "ミドルテンポ",
            "mood": "穏やか",
            "energy_level": "低い",
            "emotional_impression": "静かな印象",
        }
        raw = json.dumps(response_data, ensure_ascii=False)

        with patch("app.media.music_analyzer.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = raw
            provider = BedrockMusicProvider()
            metadata = MusicMetadata(file_name="unknown.mp3")
            result = await provider.analyze(metadata)

        assert result.get("bpm") is None
        assert result["mood"] == "穏やか"


class TestCustomProvider:
    """Test the provider pattern with a custom provider."""

    @pytest.mark.asyncio
    async def test_custom_provider_overrides_bedrock(self):
        class ExternalBpmProvider:
            async def analyze(self, metadata: MusicMetadata) -> dict:
                return {"bpm": 128, "key": "A minor"}

        bedrock_response = {
            "bpm": 120,
            "key": "C major",
            "chord_progression": "I-V-vi-IV",
            "rhythm": "4拍子",
            "tempo": "アップテンポ",
            "mood": "高揚",
            "energy_level": "高い",
            "emotional_impression": "テスト",
        }
        raw = json.dumps(bedrock_response, ensure_ascii=False)

        with patch("app.media.music_analyzer.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = raw

            # External provider comes after Bedrock, so it overrides bpm and key
            _, raw_resp = await analyze_music(
                b"fake data",
                "test.mp3",
                providers=[BedrockMusicProvider(), ExternalBpmProvider()],
            )

        # Bedrock provides rhythm/tempo/mood, external overrides bpm/key

    @pytest.mark.asyncio
    async def test_provider_failure_graceful(self):
        class FailingProvider:
            async def analyze(self, metadata: MusicMetadata) -> dict:
                raise RuntimeError("API down")

        bedrock_response = {
            "rhythm": "4拍子",
            "tempo": "ミドルテンポ",
            "mood": "穏やか",
            "energy_level": "中程度",
            "emotional_impression": "落ち着く",
        }
        raw = json.dumps(bedrock_response, ensure_ascii=False)

        with patch("app.media.music_analyzer.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = raw

            result, _ = await analyze_music(
                b"fake data",
                "test.mp3",
                providers=[BedrockMusicProvider(), FailingProvider()],
            )

        # Should succeed with Bedrock results despite failing provider
        assert result["rhythm"] == "4拍子"
        assert result["mood"] == "穏やか"


class TestAnalyzeMusic:
    @pytest.mark.asyncio
    async def test_default_provider(self):
        response_data = {
            "bpm": 100,
            "key": "D minor",
            "chord_progression": "i-iv-V-i",
            "rhythm": "3拍子",
            "tempo": "スロー",
            "mood": "哀愁",
            "energy_level": "低い",
            "emotional_impression": "切ない旋律",
        }
        raw = json.dumps(response_data, ensure_ascii=False)

        with patch("app.media.music_analyzer.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = raw
            result, raw_resp = await analyze_music(b"fake", "ballad.mp3")

        assert result["bpm"] == 100
        assert result["key"] == "D minor"
        assert result["chord_progression"] == "i-iv-V-i"
        assert result["rhythm"] == "3拍子"
        assert result["mood"] == "哀愁"

    @pytest.mark.asyncio
    async def test_defaults_on_parse_failure(self):
        with patch("app.media.music_analyzer.invoke_model", new_callable=AsyncMock) as mock:
            mock.return_value = "Not valid JSON response"
            result, _ = await analyze_music(b"fake", "test.mp3")

        assert result["rhythm"] == "解析不可"
        assert result["mood"] == "解析不可"
        assert result["bpm"] is None
