# Business Logic Model - Unit 3: Sentence Synthesis

---

## 1. 文章生成フロー

### `POST /api/synthesis/generate`

```
Client                   API              Logic           Bedrock           DB
  │                       │                │                │               │
  │ POST /generate        │                │                │               │
  │ {session_id,          │                │                │               │
  │  output_format}       │                │                │               │
  │──────────────────────►│                │                │               │
  │                       │ generate_text()│                │               │
  │                       │───────────────►│                │               │
  │                       │                │ validate_session               │
  │                       │                │ (status==emotions_selected     │
  │                       │                │  OR status==generated)         │
  │                       │                │ load_all_context()             │
  │                       │                │───────────────────────────────►│
  │                       │                │◄───────────────────────────────│
  │                       │                │ build_prompt()  │               │
  │                       │                │───────────────►│               │
  │                       │                │◄───────────────│               │
  │                       │                │ save_or_update()│               │
  │                       │                │───────────────────────────────►│
  │                       │                │ update_status() │               │
  │                       │                │ → generated     │               │
  │                       │                │───────────────────────────────►│
  │                       │◄───────────────│                │               │
  │ 201 {generated_text}  │                │                │               │
  │◄──────────────────────│                │                │               │
```

### 処理ステップ詳細

1. **セッション検証**
   - status が `emotions_selected` または `generated` であること
   - ユーザー所有であること

2. **再生成チェック**（status == `generated` の場合）
   - 既存 GeneratedText の generation_count < 10 であること
   - 10回に達している場合は ValidationError

3. **全コンテクスト読み込み**
   - MediaFile + AnalysisResult (Unit 1)
   - ContextQuestion + ContextResponse (Unit 2)
   - FreeTextInput (Unit 2, optional)
   - EmotionCandidate + EmotionSelection (Unit 2)

4. **Bedrock プロンプト構築**
   - 出力形式に応じたプロンプトテンプレート選択
   - 解析結果 + 回答 + 感情をコンテクストとして注入

5. **生成テキスト保存**
   - 初回: GeneratedText レコード新規作成（generation_count=1）
   - 再生成: 既存レコードの content / output_format / generation_count / updated_at を更新

6. **セッションステータス更新**
   - `emotions_selected` → `generated`（初回のみ）
   - 再生成時は `generated` のまま変更なし

---

## 2. Bedrock プロンプト設計

### 共通コンテクスト部分

```
■ メディア解析結果:
{analysis_summary}

■ コンテクスト設問への回答:
{responses_summary}

■ 自由記述（任意入力）:
{free_text_or_none}

■ ユーザーが選択した感情:
{selected_emotions_summary}
```

### SNS投稿形式 (output_format = "sns")

```
あなたは感情を言葉にする詩的なライターです。以下の情報を基に、
ユーザーの感情を表現するSNS投稿用の文章を生成してください。

{common_context}

出力ルール:
- 140〜280文字の短い文章
- カジュアルで共感を呼ぶトーン
- 感情の核心を端的に表現する
- 日本語で出力する

出力形式:
生成した文章のみを出力してください。説明や前置きは不要です。
```

### 日記・メモ形式 (output_format = "diary")

```
あなたは内省を言語化する日記代筆者です。以下の情報を基に、
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
生成した文章のみを出力してください。説明や前置きは不要です。
```

### レビュー記事形式 (output_format = "review")

```
あなたは文化批評家です。以下の情報を基に、
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
生成した文章のみを出力してください。説明や前置きは不要です。
```

---

## 3. コンテクスト統合ロジック

### analysis_summary 構築

画像の場合:
```
種別: 画像
主要色: {colors}  構図: {composition}  ムード: {mood}
被写体: {subjects}  雰囲気: {atmosphere}
感情的印象: {emotional_impression}
画像種別: {image_category}  様式特徴: {style_characteristics}
```

音楽の場合:
```
種別: 音楽
タイトル: {title}  アーティスト: {artist}  ジャンル: {genre}
BPM: {bpm}  キー: {key}  テンポ: {tempo}
ムード: {mood}  エネルギーレベル: {energy_level}
感情的印象: {emotional_impression}
```

### responses_summary 構築
```
Q1: {question_text} → A: {selected_choice_text}（補足: {other_text}）
Q2: {question_text} → A: {selected_choice_text}
...
```

### selected_emotions_summary 構築
```
- {emotion_label}: {emotion_description}
- {emotion_label}: {emotion_description}
...
```

---

## 4. 生成テキスト取得フロー

### `GET /api/synthesis/{session_id}`

1. **セッション検証**: ユーザー所有であること
2. **GeneratedText 取得**: session_id で検索
3. **存在しない場合**: 404 NotFound
4. **レスポンス**: generated_content, output_format, generation_count, updated_at

---

## 5. 再生成フロー

### `POST /api/synthesis/generate`（status == `generated` の場合）

再生成は初回生成と同じエンドポイントを使用。処理の違い:

1. generation_count < 10 をチェック（超過で 422 ValidationError）
2. 既存 GeneratedText を更新（INSERT ではなく UPDATE）
3. generation_count を +1
4. output_format は新しい値で上書き可能（形式変更可）
5. セッションステータスは変更なし（`generated` のまま）

---

## 6. 出力形式一覧取得フロー

### `GET /api/synthesis/formats`

認証不要の静的データ返却:

```json
{
  "formats": [
    {
      "id": "sns",
      "name": "SNS投稿",
      "description": "カジュアルな短文。",
      "min_chars": 140,
      "max_chars": 280,
      "is_default": true
    },
    {
      "id": "diary",
      "name": "日記・メモ",
      "description": "内省的で個人的な文章。",
      "min_chars": 300,
      "max_chars": 500,
      "is_default": false
    },
    {
      "id": "review",
      "name": "レビュー記事",
      "description": "構造的で分析的な長文。",
      "min_chars": 500,
      "max_chars": 1000,
      "is_default": false
    }
  ]
}
```
