import logging

from app.core.bedrock_client import invoke_model

logger = logging.getLogger(__name__)

SNS_PROMPT_TEMPLATE = """あなたは感情を言葉にする詩的なライターです。以下の情報を基に、
ユーザーの感情を表現するSNS投稿用の文章を生成してください。

{common_context}

出力ルール:
- 140〜280文字の短い文章
- カジュアルで共感を呼ぶトーン
- 感情の核心を端的に表現する
- 日本語で出力する

出力形式:
生成した文章のみを出力してください。説明や前置きは不要です。"""

DIARY_PROMPT_TEMPLATE = """あなたは内省を言語化する日記代筆者です。以下の情報を基に、
ユーザーの感情を表現する日記・メモ形式の文章を生成してください。

{common_context}

出力ルール:
- 300〜500文字の文章
- 内省的で個人的なトーン
- 「〜と感じた」「〜だった」のような過去形・回想形を使う
- 感情の揺らぎや変化を丁寧に描写する
- 絵文字は使わない
- 日本語で出力する

出力形式:
生成した文章のみを出力してください。説明や前置きは不要です。"""

REVIEW_PROMPT_TEMPLATE = """あなたは文化批評家です。以下の情報を基に、
ユーザーの感情体験をレビュー記事形式で構造的に表現してください。

{common_context}

出力ルール:
- 500〜1000文字の構造的な文章
- 分析的かつ共感的なトーン
- 段落分けを行う（2〜3段落）
- メディアの特徴と感情の関連性を論じる
- 読者に向けた推薦や感想を含める
- 絵文字は使わない
- 日本語で出力する

出力形式:
生成した文章のみを出力してください。説明や前置きは不要です。"""

PROMPT_TEMPLATES = {
    "sns": SNS_PROMPT_TEMPLATE,
    "diary": DIARY_PROMPT_TEMPLATE,
    "review": REVIEW_PROMPT_TEMPLATE,
}


def build_analysis_summary(image_analysis=None, music_analysis=None) -> str:
    """Build analysis summary for the prompt context."""
    if image_analysis:
        colors = ", ".join(image_analysis.colors) if isinstance(image_analysis.colors, list) else str(image_analysis.colors)
        subjects = ", ".join(image_analysis.subjects) if isinstance(image_analysis.subjects, list) else str(image_analysis.subjects)
        return (
            f"種別: 画像\n"
            f"主要色: {colors}  構図: {image_analysis.composition}  ムード: {image_analysis.mood}\n"
            f"被写体: {subjects}  雰囲気: {image_analysis.atmosphere}\n"
            f"感情的印象: {image_analysis.emotional_impression}\n"
            f"画像種別: {image_analysis.image_category}  様式特徴: {image_analysis.style_characteristics}"
        )
    elif music_analysis:
        return (
            f"種別: 音楽\n"
            f"タイトル: {music_analysis.title or '不明'}  アーティスト: {music_analysis.artist or '不明'}  ジャンル: {music_analysis.genre or '不明'}\n"
            f"BPM: {music_analysis.bpm or '不明'}  キー: {music_analysis.key or '不明'}  テンポ: {music_analysis.tempo}\n"
            f"ムード: {music_analysis.mood}  エネルギーレベル: {music_analysis.energy_level}\n"
            f"感情的印象: {music_analysis.emotional_impression}"
        )
    return "解析結果なし"


def build_responses_summary(responses: list, questions: list) -> str:
    """Build question-response summary for the prompt context."""
    if not responses:
        return "回答なし"

    question_map = {q.id: q for q in questions}
    lines = []
    for resp in responses:
        q = question_map.get(resp.question_id)
        q_text = q.question_text if q else "不明な設問"
        choice_text = resp.selected_choice
        if q:
            for choice in q.choices:
                if choice.get("label") == resp.selected_choice:
                    choice_text = choice.get("text", resp.selected_choice)
                    break
        line = f"Q: {q_text} → A: {choice_text}"
        if resp.other_text:
            line += f"（補足: {resp.other_text}）"
        lines.append(line)
    return "\n".join(lines)


def build_emotions_summary(candidates: list, selections: list) -> str:
    """Build selected emotions summary for the prompt context."""
    selected_ids = {s.candidate_id for s in selections}
    selected = [c for c in candidates if c.id in selected_ids]
    if not selected:
        return "感情選択なし"
    return "\n".join(f"- {c.emotion_label}: {c.emotion_description}" for c in selected)


def build_common_context(
    image_analysis=None,
    music_analysis=None,
    responses: list | None = None,
    questions: list | None = None,
    free_text: str | None = None,
    candidates: list | None = None,
    selections: list | None = None,
) -> str:
    """Build the common context block shared by all prompt templates."""
    analysis_summary = build_analysis_summary(image_analysis, music_analysis)
    responses_summary = build_responses_summary(responses or [], questions or [])
    emotions_summary = build_emotions_summary(candidates or [], selections or [])
    free_text_display = free_text if free_text else "入力なし"

    return (
        f"■ メディア解析結果:\n{analysis_summary}\n\n"
        f"■ コンテクスト設問への回答:\n{responses_summary}\n\n"
        f"■ 自由記述（任意入力）:\n{free_text_display}\n\n"
        f"■ ユーザーが選択した感情:\n{emotions_summary}"
    )


def build_prompt(output_format: str, common_context: str) -> str:
    """Build the full prompt for the given output format."""
    template = PROMPT_TEMPLATES[output_format]
    return template.format(common_context=common_context)


async def generate_text(prompt: str) -> str:
    """Call Bedrock to generate text from the prompt."""
    return await invoke_model(prompt)
