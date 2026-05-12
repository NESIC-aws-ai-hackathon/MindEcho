import pytest

from app.synthesis.text_generator import (
    build_analysis_summary,
    build_common_context,
    build_emotions_summary,
    build_prompt,
    build_responses_summary,
    PROMPT_TEMPLATES,
)


class TestBuildAnalysisSummary:
    def test_image_analysis(self):
        class FakeImage:
            colors = ["青", "白"]
            composition = "三分割"
            mood = "穏やか"
            subjects = ["海", "空"]
            atmosphere = "夏の夕暮れ"
            emotional_impression = "ノスタルジック"
            image_category = "photograph"
            style_characteristics = "風景写真"

        result = build_analysis_summary(image_analysis=FakeImage())
        assert "画像" in result
        assert "青, 白" in result
        assert "海, 空" in result
        assert "ノスタルジック" in result

    def test_music_analysis(self):
        class FakeMusic:
            title = "テスト曲"
            artist = "テスト歌手"
            genre = "ポップ"
            bpm = 120
            key = "C major"
            tempo = "ミディアム"
            mood = "明るい"
            energy_level = "高"
            emotional_impression = "元気"

        result = build_analysis_summary(music_analysis=FakeMusic())
        assert "音楽" in result
        assert "テスト曲" in result
        assert "120" in result

    def test_no_analysis(self):
        result = build_analysis_summary()
        assert "解析結果なし" in result


class TestBuildResponsesSummary:
    def test_with_responses(self):
        class FakeQ:
            id = "q1"
            question_text = "テスト設問"
            choices = [{"label": "A", "text": "選択肢A"}]

        class FakeR:
            question_id = "q1"
            selected_choice = "A"
            other_text = None

        result = build_responses_summary([FakeR()], [FakeQ()])
        assert "テスト設問" in result
        assert "選択肢A" in result

    def test_empty(self):
        result = build_responses_summary([], [])
        assert "回答なし" in result


class TestBuildEmotionsSummary:
    def test_with_selections(self):
        class FakeC:
            id = "c1"
            emotion_label = "懐かしさ"
            emotion_description = "過去を振り返る"

        class FakeS:
            candidate_id = "c1"

        result = build_emotions_summary([FakeC()], [FakeS()])
        assert "懐かしさ" in result
        assert "過去を振り返る" in result

    def test_no_selections(self):
        result = build_emotions_summary([], [])
        assert "感情選択なし" in result

    def test_unselected_excluded(self):
        class FakeC1:
            id = "c1"
            emotion_label = "懐かしさ"
            emotion_description = "D1"

        class FakeC2:
            id = "c2"
            emotion_label = "安らぎ"
            emotion_description = "D2"

        class FakeS:
            candidate_id = "c1"

        result = build_emotions_summary([FakeC1(), FakeC2()], [FakeS()])
        assert "懐かしさ" in result
        assert "安らぎ" not in result


class TestBuildCommonContext:
    def test_includes_all_sections(self):
        result = build_common_context()
        assert "メディア解析結果" in result
        assert "コンテクスト設問への回答" in result
        assert "自由記述" in result
        assert "ユーザーが選択した感情" in result

    def test_free_text_none_shows_default(self):
        result = build_common_context(free_text=None)
        assert "入力なし" in result

    def test_free_text_present(self):
        result = build_common_context(free_text="テスト自由記述")
        assert "テスト自由記述" in result


class TestBuildPrompt:
    def test_sns_format(self):
        prompt = build_prompt("sns", "テストコンテキスト")
        assert "SNS投稿" in prompt
        assert "テストコンテキスト" in prompt
        assert "140〜280" in prompt

    def test_diary_format(self):
        prompt = build_prompt("diary", "テストコンテキスト")
        assert "日記代筆者" in prompt
        assert "300〜500" in prompt

    def test_review_format(self):
        prompt = build_prompt("review", "テストコンテキスト")
        assert "文化批評家" in prompt
        assert "500〜1000" in prompt

    def test_all_formats_exist(self):
        assert "sns" in PROMPT_TEMPLATES
        assert "diary" in PROMPT_TEMPLATES
        assert "review" in PROMPT_TEMPLATES
