# Business Logic Model - Unit 1: Media Analysis

---

## 1. メディアアップロード + 解析フロー（同期処理）

### 処理シーケンス

```
Client                   API              Logic             S3         Bedrock       DB
  │                       │                │                │            │           │
  │ POST /api/media/upload│                │                │            │           │
  │ (multipart/form-data) │                │                │            │           │
  │──────────────────────►│                │                │            │           │
  │                       │ validate_file()│                │            │           │
  │                       │───────────────►│                │            │           │
  │                       │                │                │            │           │
  │                       │                │ detect_type()  │            │           │
  │                       │                │ (MIME+ext)     │            │           │
  │                       │                │                │            │           │
  │                       │                │ check_session()│            │           │
  │                       │                │───────────────────────────────────────►│
  │                       │                │ [status must be 'created']  │           │
  │                       │                │                │            │           │
  │                       │                │ upload_to_s3() │            │           │
  │                       │                │───────────────►│            │           │
  │                       │                │◄───────────────│            │           │
  │                       │                │                │            │           │
  │                       │                │ save_media_file()           │           │
  │                       │                │───────────────────────────────────────►│
  │                       │                │                │            │           │
  │                       │                │ analyze()      │            │           │
  │                       │                │───────────────────────────►│           │
  │                       │                │◄───────────────────────────│           │
  │                       │                │                │            │           │
  │                       │                │ save_analysis_result()      │           │
  │                       │                │───────────────────────────────────────►│
  │                       │                │                │            │           │
  │                       │                │ update_session_status()     │           │
  │                       │                │ (created → media_uploaded)  │           │
  │                       │                │───────────────────────────────────────►│
  │                       │                │                │            │           │
  │                       │◄───────────────│                │            │           │
  │ 201 MediaUploadResp   │                │                │            │           │
  │◄──────────────────────│                │                │            │           │
```

### 処理ステップ詳細

1. **ファイルバリデーション**
   - MIMEタイプ検証（Content-Typeヘッダー）
   - 拡張子検証（ファイル名）
   - MIMEタイプと拡張子の整合性チェック
   - ファイルサイズチェック

2. **メディア種別判定**
   - `media_type` パラメータ指定あり → そのまま使用
   - 指定なし → MIMEタイプから自動判定

3. **セッション検証**
   - セッションが存在し、ユーザー所有であること
   - セッションステータスが `created` であること

4. **S3アップロード**
   - キー生成: `{media_type}/{year}/{month}/{uuid}.{ext}`
   - ファイルデータをS3に保存

5. **MediaFileレコード作成**

6. **AI解析実行**（同期）
   - 画像: Bedrockにbase64エンコード画像を送信
   - 音楽: メタデータ抽出 → テキスト化 → Bedrockに送信

7. **解析結果保存**
   - パース後、正規化テーブルに保存

8. **セッションステータス更新**
   - `created` → `media_uploaded`

---

## 2. 画像解析フロー

### Bedrockプロンプト設計

```
あなたは画像分析の専門家です。以下の画像を詳細に分析し、
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
}
```

### 入力方法
- Bedrockのマルチモーダル入力（Claude 3）を利用
- 画像をbase64エンコードして `image` ブロックとして送信

### レスポンスパース
1. Bedrockレスポンスからテキスト部分を抽出
2. JSON部分を正規表現で抽出（```json ... ``` ブロック対応）
3. JSONパース → 各フィールドをImageAnalysisResultに格納
4. パース失敗時 → raw_responseに保存し、デフォルト値で補完

---

## 3. 音楽解析フロー

### メタデータ抽出

```python
# 疑似コード
def extract_metadata(file_data: bytes, file_name: str) -> MusicMetadata:
    # ID3タグ（MP3）、Vorbis Comment（FLAC）、AAC metadata
    metadata = parse_audio_tags(file_data)
    return MusicMetadata(
        title=metadata.get("title") or extract_from_filename(file_name),
        artist=metadata.get("artist"),
        album=metadata.get("album"),
        genre=metadata.get("genre"),
        year=metadata.get("year"),
        duration=metadata.get("duration"),
    )
```

### Bedrockプロンプト設計

```
あなたは音楽評論の専門家です。以下の楽曲メタデータから、
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
{
  "bpm": 120,
  "key": "キー（不明時はnull）",
  "chord_progression": "コード進行（不明時はnull）",
  "rhythm": "リズムの特徴",
  "tempo": "テンポの印象",
  "mood": "ムード",
  "energy_level": "エネルギーレベル",
  "emotional_impression": "感情的印象の記述"
}
```

### メタデータ不足時の対応
- タイトルがない場合: ファイル名から推定（拡張子除去、アンダースコア→スペース）
- アーティスト・ジャンルがない場合: プロンプトに「不明」と記載
- 全メタデータ空の場合: ファイル名と形式のみでBedrock推定実行

---

## 4. メディア詳細取得フロー

### `GET /api/media/{media_id}`

1. MediaFileレコードをIDで取得
2. 所有者チェック（user_id一致）
3. media_typeに応じて解析結果テーブルをJOIN
4. S3 Presigned URL生成（有効期限1時間）
5. レスポンス返却

---

## 5. セッションステータス遷移管理

### Unit 1 が担当する遷移
```
created → media_uploaded
```

### 遷移条件
- MediaFileレコードが正常に作成済み
- 解析結果レコードが正常に作成済み
- セッションの現在ステータスが `created` であること

### 不正遷移の拒否
- ステータスが `created` 以外のセッションへのアップロード → 400 Bad Request
- 既にMediaFileが存在するセッションへの再アップロード → 409 Conflict
