import json

import pytest

from app.cognitive.question_generator import (
    DEFAULT_QUESTIONS,
    _build_image_prompt,
    _build_music_prompt,
    _extract_json,
    _parse_questions,
)


class TestExtractJson:
    def test_json_code_block(self):
        text = 'Here:\n```json\n{"questions": []}\n```'
        result = _extract_json(text)
        assert result == {"questions": []}

    def test_plain_json(self):
        text = '{"questions": [{"question_text": "Q1", "choices": []}]}'
        result = _extract_json(text)
        assert result["questions"][0]["question_text"] == "Q1"

    def test_invalid_json(self):
        text = "Not JSON at all"
        result = _extract_json(text)
        assert result is None

    def test_malformed_json(self):
        text = '{"questions": ['
        result = _extract_json(text)
        assert result is None


class TestParseQuestions:
    def _make_question(self, text="テスト設問"):
        return {
            "question_text": text,
            "choices": [
                {"label": "A", "text": "選択肢A"},
                {"label": "B", "text": "選択肢B"},
                {"label": "C", "text": "選択肢C"},
                {"label": "D", "text": "選択肢D"},
                {"label": "X", "text": "その他"},
            ],
        }

    def test_valid_3_questions(self):
        data = {"questions": [self._make_question(f"Q{i}") for i in range(3)]}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_questions(raw)
        assert result is not None
        assert len(result) == 3

    def test_valid_5_questions(self):
        data = {"questions": [self._make_question(f"Q{i}") for i in range(5)]}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_questions(raw)
        assert len(result) == 5

    def test_more_than_5_truncated(self):
        data = {"questions": [self._make_question(f"Q{i}") for i in range(7)]}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_questions(raw)
        assert len(result) == 5

    def test_less_than_3_returns_none(self):
        data = {"questions": [self._make_question("Q1"), self._make_question("Q2")]}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_questions(raw)
        assert result is None

    def test_missing_question_text_skipped(self):
        questions = [self._make_question(f"Q{i}") for i in range(4)]
        questions[1] = {"choices": [{"label": "A", "text": "x"}] * 5}  # missing text
        data = {"questions": questions}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_questions(raw)
        assert result is not None
        assert len(result) == 3

    def test_insufficient_choices_skipped(self):
        questions = [self._make_question(f"Q{i}") for i in range(4)]
        questions[0]["choices"] = [{"label": "A", "text": "x"}]  # only 1 choice
        data = {"questions": questions}
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_questions(raw)
        assert len(result) == 3

    def test_no_questions_key(self):
        raw = json.dumps({"data": []})
        result = _parse_questions(raw)
        assert result is None

    def test_invalid_json_fallback(self):
        result = _parse_questions("This is not JSON")
        assert result is None


class TestBuildImagePrompt:
    def test_contains_analysis_fields(self):
        class FakeAnalysis:
            colors = ["青", "白"]
            composition = "三分割"
            mood = "穏やか"
            subjects = ["海", "空"]
            atmosphere = "夏の夕暮れ"
            texture = "滑らか"
            light_direction = "斜光"
            emotional_impression = "ノスタルジック"
            image_category = "photograph"
            style_characteristics = "風景写真"

        prompt = _build_image_prompt(FakeAnalysis())
        assert "青, 白" in prompt
        assert "三分割" in prompt
        assert "穏やか" in prompt
        assert "海, 空" in prompt
        assert "ノスタルジック" in prompt
        assert "photograph" in prompt


class TestBuildMusicPrompt:
    def test_contains_analysis_fields(self):
        class FakeAnalysis:
            title = "テスト曲"
            artist = "テストアーティスト"
            genre = "ポップ"
            bpm = 120
            key = "C major"
            chord_progression = "I-V-vi-IV"
            rhythm = "4/4拍子"
            tempo = "ミディアム"
            mood = "明るい"
            energy_level = "高"
            emotional_impression = "元気が出る"

        prompt = _build_music_prompt(FakeAnalysis())
        assert "テスト曲" in prompt
        assert "テストアーティスト" in prompt
        assert "120" in prompt
        assert "C major" in prompt
        assert "I-V-vi-IV" in prompt

    def test_none_fields_show_unknown(self):
        class FakeAnalysis:
            title = None
            artist = None
            genre = None
            bpm = None
            key = None
            chord_progression = None
            rhythm = "4/4"
            tempo = "速い"
            mood = "激しい"
            energy_level = "高"
            emotional_impression = "アドレナリン"

        prompt = _build_music_prompt(FakeAnalysis())
        assert "不明" in prompt


class TestDefaultQuestions:
    def test_has_3_questions(self):
        assert len(DEFAULT_QUESTIONS) == 3

    def test_each_has_5_choices(self):
        for q in DEFAULT_QUESTIONS:
            assert len(q["choices"]) == 5
            labels = [c["label"] for c in q["choices"]]
            assert "X" in labels
