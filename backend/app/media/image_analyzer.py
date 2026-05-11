import base64
import json
import logging
import re

from app.core.bedrock_client import get_bedrock_client
from app.core.config import settings

logger = logging.getLogger(__name__)

IMAGE_ANALYSIS_PROMPT = """あなたは画像分析の専門家です。以下の画像を詳細に分析し、
指定されたJSON形式で結果を返してください。

分析項目:
1. colors: 画像の主要色を3〜5色、日本語の色名で記述（例: 深い紺色、暖かいオレンジ）
2. composition: 構図の特徴を簡潔に記述
3. mood: 画像全体のムードを一言で
4. subjects: 主要な被写体をリストで
5. atmosphere: 雰囲気を1〜2文で記述
6. texture: テクスチャの特徴を記述
7. light_direction: 光の方向や質を記述
8. emotional_impression: この画像が見る者に与える感情的印象を1〜2文で
9. image_category: この画像の種別を以下から1つ選択
   - "photograph"（写真）
   - "painting"（絵画）
   - "illustration"（イラスト）
   - "digital_art"（デジタルアート/CG）
   - "other"（その他）
10. style_characteristics: 種別に応じた詳細な様式・画風の特徴を記述
   - 写真の場合: 撮影スタイル（ポートレート、風景、ストリートスナップ等）、技法（浅い被写界深度、長時間露光等）
   - 絵画の場合: 美術様式（バロック、ロマン主義、印象派、抽象表現主義等）、技法（明暗法、点描等）
   - イラストの場合: 画風（アニメ調、水彩風、厚塗り、線画、ベクター等）
   - デジタルアートの場合: スタイル（フォトリアル、ローポリ、グリッチアート、コンセプトアート等）

出力形式（必ずこのJSON形式で）:
{
  "colors": ["色1", "色2", ...],
  "composition": "構図の説明",
  "mood": "ムード",
  "subjects": ["被写体1", "被写体2", ...],
  "atmosphere": "雰囲気の説明",
  "texture": "テクスチャの特徴",
  "light_direction": "光の方向・質",
  "emotional_impression": "感情的印象の記述",
  "image_category": "種別",
  "style_characteristics": "詳細な様式・画風特徴の記述"
}"""

ANALYSIS_FIELDS = [
    "colors", "composition", "mood", "subjects", "atmosphere",
    "texture", "light_direction", "emotional_impression",
    "image_category", "style_characteristics",
]

DEFAULT_VALUES: dict[str, str | list[str]] = {
    "colors": ["不明"],
    "composition": "解析不可",
    "mood": "解析不可",
    "subjects": ["不明"],
    "atmosphere": "解析不可",
    "texture": "解析不可",
    "light_direction": "解析不可",
    "emotional_impression": "解析不可",
    "image_category": "other",
    "style_characteristics": "解析不可",
}


def _extract_json(text: str) -> dict | None:
    """Extract JSON from text, handling ```json blocks."""
    # Try ```json ... ``` block first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try raw JSON
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _parse_response(raw_response: str) -> dict:
    """Parse Bedrock response into analysis fields with fallback defaults."""
    parsed = _extract_json(raw_response)
    if parsed is None:
        logger.warning("Failed to parse image analysis JSON, using defaults")
        return {field: DEFAULT_VALUES[field] for field in ANALYSIS_FIELDS}

    result = {}
    for field in ANALYSIS_FIELDS:
        if field in parsed and parsed[field]:
            result[field] = parsed[field]
        else:
            result[field] = DEFAULT_VALUES[field]

    return result


async def analyze_image(file_data: bytes, mime_type: str) -> tuple[dict, str]:
    """Analyze an image using Bedrock multimodal input.

    Returns:
        Tuple of (analysis_dict, raw_response)
    """
    b64_data = base64.b64encode(file_data).decode("utf-8")

    # Map MIME type to Bedrock media type
    media_type_map = {
        "image/jpeg": "image/jpeg",
        "image/png": "image/png",
        "image/webp": "image/webp",
        "image/gif": "image/gif",
    }
    bedrock_media_type = media_type_map.get(mime_type, "image/jpeg")

    client = get_bedrock_client()
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": bedrock_media_type,
                            "data": b64_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": IMAGE_ANALYSIS_PROMPT,
                    },
                ],
            }
        ],
    })

    response = client.invoke_model(
        modelId=settings.aws_bedrock_model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )

    response_body = json.loads(response["body"].read())
    raw_response = response_body["content"][0]["text"]

    analysis = _parse_response(raw_response)
    return analysis, raw_response
