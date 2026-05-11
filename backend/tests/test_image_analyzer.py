import json

import pytest

from app.media.image_analyzer import _extract_json, _parse_response, ANALYSIS_FIELDS, DEFAULT_VALUES


class TestExtractJson:
    def test_json_code_block(self):
        text = 'Here is the result:\n```json\n{"colors": ["red"]}\n```'
        result = _extract_json(text)
        assert result == {"colors": ["red"]}

    def test_plain_json(self):
        text = '{"mood": "calm"}'
        result = _extract_json(text)
        assert result == {"mood": "calm"}

    def test_json_in_text(self):
        text = 'Analysis result:\n{"mood": "happy", "colors": ["blue"]}\nEnd.'
        result = _extract_json(text)
        assert result["mood"] == "happy"

    def test_invalid_json(self):
        text = "This is not JSON at all."
        result = _extract_json(text)
        assert result is None

    def test_malformed_json(self):
        text = '{"colors": ["red"'
        result = _extract_json(text)
        assert result is None


class TestParseResponse:
    def test_full_valid_response(self):
        data = {
            "colors": ["深い紺色", "暖かいオレンジ"],
            "composition": "三分割構図",
            "mood": "静寂",
            "subjects": ["山", "湖"],
            "atmosphere": "夕暮れの静かな郊外",
            "texture": "滑らか",
            "light_direction": "逆光",
            "emotional_impression": "懐かしさを感じる",
            "image_category": "photograph",
            "style_characteristics": "風景写真、自然光",
        }
        raw = json.dumps(data, ensure_ascii=False)
        result = _parse_response(raw)

        assert result["colors"] == ["深い紺色", "暖かいオレンジ"]
        assert result["mood"] == "静寂"
        assert result["image_category"] == "photograph"
        assert result["style_characteristics"] == "風景写真、自然光"

    def test_partial_response_fills_defaults(self):
        data = {"colors": ["red"], "mood": "happy"}
        raw = json.dumps(data)
        result = _parse_response(raw)

        assert result["colors"] == ["red"]
        assert result["mood"] == "happy"
        assert result["composition"] == DEFAULT_VALUES["composition"]
        assert result["image_category"] == DEFAULT_VALUES["image_category"]

    def test_unparseable_response_returns_all_defaults(self):
        result = _parse_response("This is not JSON")

        for field in ANALYSIS_FIELDS:
            assert result[field] == DEFAULT_VALUES[field]

    def test_empty_field_gets_default(self):
        data = {"colors": [], "mood": ""}
        raw = json.dumps(data)
        result = _parse_response(raw)

        assert result["colors"] == DEFAULT_VALUES["colors"]
        assert result["mood"] == DEFAULT_VALUES["mood"]

    def test_code_block_response(self):
        data = {
            "colors": ["青"],
            "composition": "中央配置",
            "mood": "穏やか",
            "subjects": ["空"],
            "atmosphere": "朝の静けさ",
            "texture": "柔らかい",
            "light_direction": "自然光",
            "emotional_impression": "安らぎ",
            "image_category": "painting",
            "style_characteristics": "印象派、筆タッチ",
        }
        raw = f"```json\n{json.dumps(data, ensure_ascii=False)}\n```"
        result = _parse_response(raw)

        assert result["image_category"] == "painting"
        assert result["style_characteristics"] == "印象派、筆タッチ"
