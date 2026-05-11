import json
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.models import EmotionCandidate
from app.core.bedrock_client import invoke_model

logger = logging.getLogger(__name__)

EMOTION_GENERATION_PROMPT = """あなたは感情分析の専門家です。以下の情報を基に、ユーザーが感じていると
思われる感情の選択肢を3〜5個生成してください。

■ メディア解析結果:
{analysis_summary}

■ コンテクスト設問への回答:
{responses_summary}

■ 自由記述（任意入力）:
{free_text_or_none}

感情選択肢のルール:
- 3〜5個の感情を生成
- 各感情にはラベル（短い名前）と説明文を付ける
- 多様な感情（ポジティブ/ネガティブ/ニュートラル）を含める
- メディアの特徴と回答内容に基づく具体的な感情にする
- 日本語で出力する

出力形式（必ずこのJSON形式で）:
{{
  "emotions": [
    {{
      "emotion_label": "感情名",
      "emotion_description": "この感情を選ぶとどのような文章が生成されるかの説明"
    }}
  ]
}}"""

DEFAULT_EMOTIONS = [
    {"emotion_label": "懐かしさ", "emotion_description": "過去を振り返る温かい感情"},
    {"emotion_label": "安らぎ", "emotion_description": "穏やかで落ち着いた感情"},
    {"emotion_label": "高揚感", "emotion_description": "わくわくする興奮した感情"},
    {"emotion_label": "切なさ", "emotion_description": "甘く痛い感傷的な感情"},
    {"emotion_label": "感謝", "emotion_description": "ありがたいと思う感情"},
]


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


def _build_analysis_summary(
    image_analysis=None, music_analysis=None
) -> str:
    """Build analysis summary text for emotion prompt."""
    if image_analysis:
        colors = ", ".join(image_analysis.colors) if isinstance(image_analysis.colors, list) else str(image_analysis.colors)
        subjects = ", ".join(image_analysis.subjects) if isinstance(image_analysis.subjects, list) else str(image_analysis.subjects)
        return (
            f"種別: 画像\n"
            f"主要色: {colors}\n"
            f"構図: {image_analysis.composition}\n"
            f"ムード: {image_analysis.mood}\n"
            f"被写体: {subjects}\n"
            f"雰囲気: {image_analysis.atmosphere}\n"
            f"感情的印象: {image_analysis.emotional_impression}\n"
            f"画像種別: {image_analysis.image_category}\n"
            f"様式特徴: {image_analysis.style_characteristics}"
        )
    elif music_analysis:
        return (
            f"種別: 音楽\n"
            f"タイトル: {music_analysis.title or '不明'}\n"
            f"アーティスト: {music_analysis.artist or '不明'}\n"
            f"ジャンル: {music_analysis.genre or '不明'}\n"
            f"BPM: {music_analysis.bpm or '不明'}\n"
            f"キー: {music_analysis.key or '不明'}\n"
            f"リズム: {music_analysis.rhythm}\n"
            f"テンポ: {music_analysis.tempo}\n"
            f"ムード: {music_analysis.mood}\n"
            f"エネルギーレベル: {music_analysis.energy_level}\n"
            f"感情的印象: {music_analysis.emotional_impression}"
        )
    return "解析結果なし"


def _build_responses_summary(responses: list, questions: list) -> str:
    """Build responses summary for emotion prompt."""
    if not responses:
        return "回答なし"

    question_map = {q.id: q for q in questions}
    lines = []
    for resp in responses:
        q = question_map.get(resp.question_id)
        q_text = q.question_text if q else "不明な設問"
        # Find the choice text
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


def _parse_emotions(response_text: str) -> list[dict] | None:
    """Parse Bedrock response into emotion list."""
    data = _extract_json(response_text)
    if data is None:
        return None

    emotions = data.get("emotions")
    if not isinstance(emotions, list) or len(emotions) < 3:
        return None

    valid_emotions = []
    for e in emotions:
        if not isinstance(e, dict):
            continue
        if "emotion_label" not in e or "emotion_description" not in e:
            continue
        valid_emotions.append(e)

    if len(valid_emotions) < 3:
        return None

    return valid_emotions[:5]


async def generate_emotions(
    db: AsyncSession,
    session_id: str,
    image_analysis=None,
    music_analysis=None,
    responses: list | None = None,
    questions: list | None = None,
    free_text: str | None = None,
) -> list[EmotionCandidate]:
    """Generate emotion candidates based on analysis and user responses.

    Returns list of saved EmotionCandidate records.
    """
    analysis_summary = _build_analysis_summary(image_analysis, music_analysis)
    responses_summary = _build_responses_summary(responses or [], questions or [])
    free_text_display = free_text if free_text else "入力なし"

    prompt = EMOTION_GENERATION_PROMPT.format(
        analysis_summary=analysis_summary,
        responses_summary=responses_summary,
        free_text_or_none=free_text_display,
    )

    try:
        response_text = await invoke_model(prompt)
        emotions_data = _parse_emotions(response_text)
    except Exception:
        logger.error("Bedrock emotion generation failed for session %s", session_id, exc_info=True)
        emotions_data = None

    if emotions_data is None:
        logger.warning("Using default emotions for session %s", session_id)
        emotions_data = DEFAULT_EMOTIONS

    return await _save_emotions(db, session_id, emotions_data)


async def _save_emotions(
    db: AsyncSession, session_id: str, emotions_data: list[dict]
) -> list[EmotionCandidate]:
    """Save emotion data as EmotionCandidate records."""
    candidates = []
    for i, e_data in enumerate(emotions_data, start=1):
        candidate = EmotionCandidate(
            session_id=session_id,
            candidate_order=i,
            emotion_label=e_data["emotion_label"],
            emotion_description=e_data["emotion_description"],
        )
        db.add(candidate)
        candidates.append(candidate)

    await db.flush()
    return candidates
