# Business Logic Model - Unit 2: Cognitive Mapping

---

## 1. コンテクスト設問生成フロー（メディア解析完了時に同期実行）

### 処理シーケンス

```
(Unit 1 upload_and_analyze の最終ステップとして実行)

Logic (media)          Cognitive Logic         Bedrock              DB
     │                       │                    │                 │
     │ generate_questions()  │                    │                 │
     │──────────────────────►│                    │                 │
     │                       │ build_prompt()     │                 │
     │                       │ (解析結果を入力)    │                 │
     │                       │───────────────────►│                 │
     │                       │◄───────────────────│                 │
     │                       │ parse_questions()  │                 │
     │                       │ save_questions()   │                 │
     │                       │──────────────────────────────────────►│
     │◄──────────────────────│                    │                 │
```

### 処理ステップ詳細

1. **解析結果取得**
   - セッションに紐づく MediaFile + AnalysisResult を読み込み
   - 画像: ImageAnalysisResult の全10項目
   - 音楽: MusicAnalysisResult の全8項目 + メタデータ

2. **Bedrockプロンプト構築**
   - 解析結果をテキスト化してコンテクストとして渡す
   - 設問数: 3〜5問（プロンプトで指定）
   - 各設問: 選択肢4〜5個 + 「その他」

3. **レスポンスパース**
   - JSON形式で受領
   - 各設問を ContextQuestion レコードとして保存

4. **セッションステータス**
   - この時点ではステータス変更なし（`media_uploaded` のまま）
   - 設問生成はアップロードフローの一部

---

## 2. コンテクスト設問生成 — Bedrockプロンプト設計

### 画像の場合

```
あなたはユーザーの感情を引き出すインタビュアーです。
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
{
  "questions": [
    {
      "question_text": "設問文",
      "choices": [
        {"label": "A", "text": "選択肢A"},
        {"label": "B", "text": "選択肢B"},
        {"label": "C", "text": "選択肢C"},
        {"label": "D", "text": "選択肢D"},
        {"label": "X", "text": "その他"}
      ]
    }
  ]
}
```

### 音楽の場合

```
あなたはユーザーの感情を引き出すインタビュアーです。
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
{
  "questions": [
    {
      "question_text": "設問文",
      "choices": [
        {"label": "A", "text": "選択肢A"},
        {"label": "B", "text": "選択肢B"},
        {"label": "C", "text": "選択肢C"},
        {"label": "D", "text": "選択肢D"},
        {"label": "X", "text": "その他"}
      ]
    }
  ]
}
```

### レスポンスパース
1. Bedrockレスポンスからテキスト部分を抽出
2. JSON部分を正規表現で抽出（```json ... ``` ブロック対応）
3. JSONパース → 各設問を ContextQuestion レコードに格納
4. パース失敗時 → デフォルト3問（汎用的な設問）を生成

### デフォルト設問（フォールバック）
```json
[
  {
    "question_text": "このメディアを選んだ理由は何ですか？",
    "choices": [
      {"label": "A", "text": "気分を表現したいから"},
      {"label": "B", "text": "誰かに共有したいから"},
      {"label": "C", "text": "記録として残したいから"},
      {"label": "D", "text": "特に理由はない"},
      {"label": "X", "text": "その他"}
    ]
  },
  {
    "question_text": "今のあなたの気持ちに最も近いのは？",
    "choices": [
      {"label": "A", "text": "穏やかな気持ち"},
      {"label": "B", "text": "少し興奮している"},
      {"label": "C", "text": "物思いにふけっている"},
      {"label": "D", "text": "何かを伝えたい"},
      {"label": "X", "text": "その他"}
    ]
  },
  {
    "question_text": "生成される文章をどのように使いたいですか？",
    "choices": [
      {"label": "A", "text": "SNSに投稿したい"},
      {"label": "B", "text": "日記に書き留めたい"},
      {"label": "C", "text": "誰かに送りたい"},
      {"label": "D", "text": "自分だけで読みたい"},
      {"label": "X", "text": "その他"}
    ]
  }
]
```

---

## 3. 設問回答受付フロー

### `POST /api/cognitive/responses`

```
Client                   API              Logic              DB
  │                       │                │                 │
  │ POST /responses       │                │                 │
  │ {responses: [...]}    │                │                 │
  │──────────────────────►│                │                 │
  │                       │ submit_responses()               │
  │                       │───────────────►│                 │
  │                       │                │ validate_session │
  │                       │                │ validate_all_answered │
  │                       │                │ save_responses() │
  │                       │                │────────────────►│
  │                       │◄───────────────│                 │
  │ 201 Created           │                │                 │
  │◄──────────────────────│                │                 │
```

### 処理ステップ
1. **セッション検証**: status == `media_uploaded`, ユーザー所有
2. **全問回答検証**: セッションの全ContextQuestionに対して回答があること
3. **回答バリデーション**: selected_choice がその設問の choices に含まれること
4. **other_text検証**: selected_choice == "X" の場合のみ other_text 必須（200文字以内）
5. **回答保存**: ContextResponse レコード一括保存
6. **注**: セッションステータスは変更しない（自由記述入力または感情生成のタイミングで更新）

---

## 4. 自由記述入力フロー

### `POST /api/cognitive/free-text`

1. **セッション検証**: status == `media_uploaded`, ユーザー所有
2. **全問回答済み検証**: 全設問に回答があること
3. **重複チェック**: 既にFreeTextInputが存在しないこと
4. **バリデーション**: content が 1〜500文字
5. **保存**: FreeTextInput レコード作成

---

## 5. 設問回答完了 + 感情選択肢生成フロー

### `POST /api/cognitive/complete-questions`

設問回答（+ 任意の自由記述）が完了した後に呼び出し、感情選択肢を生成する。

```
Client                   API              Logic           Bedrock           DB
  │                       │                │                │               │
  │ POST /complete-questions               │                │               │
  │──────────────────────►│                │                │               │
  │                       │ complete_and_generate_emotions()│               │
  │                       │───────────────►│                │               │
  │                       │                │ validate_all_answered          │
  │                       │                │ load_context() │               │
  │                       │                │───────────────►│               │
  │                       │                │◄───────────────│               │
  │                       │                │ parse_emotions()               │
  │                       │                │ save_candidates()              │
  │                       │                │────────────────────────────────►│
  │                       │                │ update_status()│               │
  │                       │                │ → questions_answered           │
  │                       │                │────────────────────────────────►│
  │                       │◄───────────────│                │               │
  │ 201 {candidates: [...]}               │                │               │
  │◄──────────────────────│                │                │               │
```

### 処理ステップ
1. **セッション検証**: status == `media_uploaded`, ユーザー所有
2. **全問回答検証**: 全設問に回答済みであること
3. **解析結果 + 回答 + 自由記述を収集**
4. **Bedrock で感情選択肢を生成**（3〜5個）
5. **EmotionCandidate レコード保存**
6. **セッションステータス更新**: `media_uploaded` → `questions_answered`
7. **レスポンス**: 生成された感情候補リストを返却

---

## 6. 感情選択肢生成 — Bedrockプロンプト設計

```
あなたは感情分析の専門家です。以下の情報を基に、ユーザーが感じていると
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
{
  "emotions": [
    {
      "emotion_label": "感情名",
      "emotion_description": "この感情を選ぶとどのような文章が生成されるかの説明"
    }
  ]
}
```

### レスポンスパース
1. JSON抽出 → 各感情を EmotionCandidate レコードに格納
2. パース失敗時 → デフォルト5感情で補完

### デフォルト感情（フォールバック）
- 「懐かしさ」— 過去を振り返る温かい感情
- 「安らぎ」— 穏やかで落ち着いた感情
- 「高揚感」— わくわくする興奮した感情
- 「切なさ」— 甘く痛い感傷的な感情
- 「感謝」— ありがたいと思う感情

---

## 7. 感情選択受付フロー

### `POST /api/cognitive/emotions`

1. **セッション検証**: status == `questions_answered`, ユーザー所有
2. **候補存在検証**: 選択された candidate_id が全てそのセッションの EmotionCandidate であること
3. **最低1つ検証**: 1つ以上選択されていること
4. **重複チェック**: 同じ候補を2回選択していないこと
5. **EmotionSelection レコード保存**
6. **セッションステータス更新**: `questions_answered` → `emotions_selected`

---

## 8. 設問・感情取得フロー

### `GET /api/cognitive/questions/{session_id}`
- セッションの全ContextQuestionを question_order 順で返却
- 回答済みの場合は ContextResponse も含む

### `GET /api/cognitive/emotions/{session_id}`
- セッションの全EmotionCandidateを candidate_order 順で返却
- 選択済みの場合は EmotionSelection も含む
