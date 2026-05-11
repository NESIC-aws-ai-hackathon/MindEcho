import json

import pytest

from app.cognitive.emotion_generator import (
    DEFAULT_EMOTIONS,
    _build_analysis_summary,
    _build_responses_summary,
    _extract_json,
    _parse_emotions,
)


class TestExtractJson:
    def test_json_code_block(self):
        text = '```json\n{"emotions": []}\n```'
        result = _extract_json(text)
        assert result == {"emotions": []}

    def test_plain_json(self):
        text = '{"emotions": [{"emotion_label": "x", "emotion_description": "y"}]}'
        result = _extract_json(text)
        assert result["emotions"][0]["emotion_label"] == "x"

    def test_invalid(self):
        assert _extract_json("no json here") is None


class TestParseEmotions:
    def _make_emotion(self, label="テスト感情"):
        return {"emotion_label": label, "emotion_description": f"{label}の説明"}

    def test_valid_3_emotions(self):
        data = {"emotions": [self._make_emotion(f"E{i}") for i in range(3)]}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_emotions(raw)
        assert result is not None
        assert len(result) == 3

    def test_valid_5_emotions(self):
        data = {"emotions": [self._make_emotion(f"E{i}") for i in range(5)]}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_emotions(raw)
        assert len(result) == 5

    def test_more_than_5_truncated(self):
        data = {"emotions": [self._make_emotion(f"E{i}") for i in range(7)]}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_emotions(raw)
        assert len(result) == 5

    def test_less_than_3_returns_none(self):
        data = {"emotions": [self._make_emotion("E1"), self._make_emotion("E2")]}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_emotions(raw)
        assert result is None

    def test_missing_label_skipped(self):
        emotions = [self._make_emotion(f"E{i}") for i in range(4)]
        emotions[1] = {"emotion_description": "no label"}
        data = {"emotions": emotions}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_emotions(raw)
        assert len(result) == 3

    def test_no_emotions_key(self):
        raw = json.dumps({"data": []})
        result = _parse_emotions(raw)
        assert result is None

    def test_invalid_json(self):
        result = _parse_emotions("not json")
        assert result is None


class TestBuildAnalysisSummary:
    def test_image_analysis(self):
        class FakeImage:
            colors = ["赤", "青"]
            composition = "中央寄せ"
            mood = "明るい"
            subjects = ["花"]
            atmosphere = "春の庭"
            emotional_impression = "幸福感"
            image_category = "photograph"
            style_characteristics = "マクロ撮影"

        result = _build_analysis_summary(image_analysis=FakeImage())
        assert "画像" in result
        assert "赤, 青" in result
        assert "花" in result

    def test_music_analysis(self):
        class FakeMusic:
            title = "曲名"
            artist = "歌手"
            genre = "ロック"
            bpm = 140
            key = "E minor"
            rhythm = "8ビート"
            tempo = "速い"
            mood = "激しい"
            energy_level = "高"
            emotional_impression = "力強い"

        result = _build_analysis_summary(music_analysis=FakeMusic())
        assert "音楽" in result
        assert "曲名" in result
        assert "140" in result

    def test_no_analysis(self):
        result = _build_analysis_summary()
        assert "解析結果なし" in result


class TestBuildResponsesSummary:
    def test_empty_responses(self):
        result = _build_responses_summary([], [])
        assert "回答なし" in result

    def test_with_responses(self):
        class FakeQuestion:
            id = "q1"
            question_text = "テスト設問"
            choices = [{"label": "A", "text": "選択肢A"}]

        class FakeResponse:
            question_id = "q1"
            selected_choice = "A"
            other_text = None

        result = _build_responses_summary([FakeResponse()], [FakeQuestion()])
        assert "テスト設問" in result
        assert "選択肢A" in result

    def test_with_other_text(self):
        class FakeQuestion:
            id = "q1"
            question_text = "設問X"
            choices = [{"label": "X", "text": "その他"}]

        class FakeResponse:
            question_id = "q1"
            selected_choice = "X"
            other_text = "自由入力テスト"

        result = _build_responses_summary([FakeResponse()], [FakeQuestion()])
        assert "自由入力テスト" in result


class TestDefaultEmotions:
    def test_has_5_emotions(self):
        assert len(DEFAULT_EMOTIONS) == 5

    def test_each_has_label_and_description(self):
        for e in DEFAULT_EMOTIONS:
            assert "emotion_label" in e
            assert "emotion_description" in e
            assert len(e["emotion_label"]) > 0
