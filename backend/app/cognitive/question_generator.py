import json
import logging
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cognitive.models import ContextQuestion
from app.core.bedrock_client import get_bedrock_client, invoke_model
from app.core.config import settings
from app.media.models import ImageAnalysisResult, MediaFile, MusicAnalysisResult

logger = logging.getLogger(__name__)

IMAGE_QUESTION_PROMPT = """あなたはユーザーの感情を引き出すインタビュアーです。
以下の画像解析結果を参考に、ユーザーがこの画像についてどのような文脈で
捉えているかを理解するための設問を3〜5問生成してください。

画像解析結果:
- 主要色: {colors}
- 構図: {composition}
- ムード: {mood}
- 被写体: {subjects}
- 雰囲気: {atmosphere}
- テクスチャ: {texture}
- 光の方向: {light_direction}
- 感情的印象: {emotional_impression}
- 画像種別: {image_category}
- 様式特徴: {style_characteristics}

設問のルール:
- 各設問は選択式（A〜D + X「その他」）の5択
- 設問はユーザーの状況・意図・感情に関するものにする
- 画像の特徴に基づいた具体的な設問にする
- 日本語で出力する

出力形式（必ずこのJSON形式で）:
{{
  "questions": [
    {{
      "question_text": "設問文",
      "choices": [
        {{"label": "A", "text": "選択肢A"}},
        {{"label": "B", "text": "選択肢B"}},
        {{"label": "C", "text": "選択肢C"}},
        {{"label": "D", "text": "選択肢D"}},
        {{"label": "X", "text": "その他"}}
      ]
    }}
  ]
}}"""

MUSIC_QUESTION_PROMPT = """あなたはユーザーの感情を引き出すインタビュアーです。
以下の楽曲解析結果を参考に、ユーザーがこの楽曲についてどのような文脈で
聴いているかを理解するための設問を3〜5問生成してください。

楽曲解析結果:
- タイトル: {title}
- アーティスト: {artist}
- ジャンル: {genre}
- BPM: {bpm}
- キー: {key}
- コード進行: {chord_progression}
- リズム: {rhythm}
- テンポ: {tempo}
- ムード: {mood}
- エネルギーレベル: {energy_level}
- 感情的印象: {emotional_impression}

設問のルール:
- 各設問は選択式（A〜D + X「その他」）の5択
- 設問はユーザーの状況・意図・感情に関するものにする
- 楽曲の特徴に基づいた具体的な設問にする
- 日本語で出力する

出力形式（必ずこのJSON形式で）:
{{
  "questions": [
    {{
      "question_text": "設問文",
      "choices": [
        {{"label": "A", "text": "選択肢A"}},
        {{"label": "B", "text": "選択肢B"}},
        {{"label": "C", "text": "選択肢C"}},
        {{"label": "D", "text": "選択肢D"}},
        {{"label": "X", "text": "その他"}}
      ]
    }}
  ]
}}"""

DEFAULT_QUESTIONS = [
    {
        "question_text": "このメディアを選んだ理由は何ですか？",
        "choices": [
            {"label": "A", "text": "気分を表現したいから"},
            {"label": "B", "text": "誰かに共有したいから"},
            {"label": "C", "text": "記録として残したいから"},
            {"label": "D", "text": "特に理由はない"},
            {"label": "X", "text": "その他"},
        ],
    },
    {
        "question_text": "今のあなたの気持ちに最も近いのは？",
        "choices": [
            {"label": "A", "text": "穏やかな気持ち"},
            {"label": "B", "text": "少し興奮している"},
            {"label": "C", "text": "物思いにふけっている"},
            {"label": "D", "text": "何かを伝えたい"},
            {"label": "X", "text": "その他"},
        ],
    },
    {
        "question_text": "生成される文章をどのように使いたいですか？",
        "choices": [
            {"label": "A", "text": "SNSに投稿したい"},
            {"label": "B", "text": "日記に書き留めたい"},
            {"label": "C", "text": "誰かに送りたい"},
            {"label": "D", "text": "自分だけで読みたい"},
            {"label": "X", "text": "その他"},
        ],
    },
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


def _build_image_prompt(analysis: ImageAnalysisResult) -> str:
    """Build question generation prompt from image analysis."""
    colors = ", ".join(analysis.colors) if isinstance(analysis.colors, list) else str(analysis.colors)
    subjects = ", ".join(analysis.subjects) if isinstance(analysis.subjects, list) else str(analysis.subjects)
    return IMAGE_QUESTION_PROMPT.format(
        colors=colors,
        composition=analysis.composition,
        mood=analysis.mood,
        subjects=subjects,
        atmosphere=analysis.atmosphere,
        texture=analysis.texture,
        light_direction=analysis.light_direction,
        emotional_impression=analysis.emotional_impression,
        image_category=analysis.image_category,
        style_characteristics=analysis.style_characteristics,
    )


def _build_music_prompt(analysis: MusicAnalysisResult) -> str:
    """Build question generation prompt from music analysis."""
    return MUSIC_QUESTION_PROMPT.format(
        title=analysis.title or "不明",
        artist=analysis.artist or "不明",
        genre=analysis.genre or "不明",
        bpm=analysis.bpm or "不明",
        key=analysis.key or "不明",
        chord_progression=analysis.chord_progression or "不明",
        rhythm=analysis.rhythm,
        tempo=analysis.tempo,
        mood=analysis.mood,
        energy_level=analysis.energy_level,
        emotional_impression=analysis.emotional_impression,
    )


def _parse_questions(response_text: str) -> list[dict] | None:
    """Parse Bedrock response into question list."""
    data = _extract_json(response_text)
    if data is None:
        return None

    questions = data.get("questions")
    if not isinstance(questions, list) or len(questions) < 3:
        return None

    # Validate structure
    valid_questions = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        if "question_text" not in q or "choices" not in q:
            continue
        if not isinstance(q["choices"], list) or len(q["choices"]) < 4:
            continue
        valid_questions.append(q)

    if len(valid_questions) < 3:
        return None

    # Limit to 5 questions
    return valid_questions[:5]


async def generate_questions(
    db: AsyncSession,
    session_id: str,
    media_file: MediaFile,
    image_analysis: ImageAnalysisResult | None,
    music_analysis: MusicAnalysisResult | None,
) -> list[ContextQuestion]:
    """Generate context questions based on media analysis results.

    Returns list of saved ContextQuestion records.
    """
    # Build prompt
    if image_analysis:
        prompt = _build_image_prompt(image_analysis)
    elif music_analysis:
        prompt = _build_music_prompt(music_analysis)
    else:
        logger.warning("No analysis result for session %s, using defaults", session_id)
        questions_data = DEFAULT_QUESTIONS
        return await _save_questions(db, session_id, questions_data)

    # Call Bedrock
    try:
        response_text = await invoke_model(prompt)
        questions_data = _parse_questions(response_text)
    except Exception:
        logger.error("Bedrock question generation failed for session %s", session_id, exc_info=True)
        questions_data = None

    # Fallback to defaults
    if questions_data is None:
        logger.warning("Using default questions for session %s", session_id)
        questions_data = DEFAULT_QUESTIONS

    return await _save_questions(db, session_id, questions_data)


async def _save_questions(
    db: AsyncSession, session_id: str, questions_data: list[dict]
) -> list[ContextQuestion]:
    """Save question data as ContextQuestion records."""
    questions = []
    for i, q_data in enumerate(questions_data, start=1):
        question = ContextQuestion(
            session_id=session_id,
            question_order=i,
            question_text=q_data["question_text"],
            choices=q_data["choices"],
        )
        db.add(question)
        questions.append(question)

    await db.flush()
    return questions
