# Business Rules - Unit 2: Cognitive Mapping

---

## 1. コンテクスト設問ルール

### BR-COG-01: 設問生成数
- 1セッションにつき3〜5問を生成
- Bedrockレスポンスが3問未満の場合: デフォルト設問で補完し3問に
- Bedrockレスポンスが5問超の場合: 先頭5問のみ採用

### BR-COG-02: 設問生成タイミング
- メディアアップロード + 解析の同期フロー内で生成
- Unit 1 の upload_and_analyze 成功後に自動実行
- 設問生成失敗時: デフォルト3問でフォールバック（アップロード自体は成功扱い）

### BR-COG-03: 設問選択肢構造
- 各設問は4〜5個の通常選択肢 + 「その他(X)」で構成
- 選択肢ラベル: A, B, C, D, (E), X
- 「その他(X)」は常に最後の選択肢

### BR-COG-04: 設問の一意性
- 1セッションにつき設問セットは1回のみ生成
- 再生成は不可（新しいセッションを作成する必要がある）

---

## 2. 設問回答ルール

### BR-COG-05: 回答必須
- 全設問への回答が必須
- 未回答の設問がある場合は回答を受け付けない（一括送信）
- エラー: 422 Validation Error「全設問への回答が必要です」

### BR-COG-06: 回答バリデーション
- selected_choice はその設問の choices に含まれるラベルであること
- 存在しないラベル: 422 Validation Error
- 空文字列: 422 Validation Error

### BR-COG-07: 「その他」自由記述ルール
- selected_choice == "X" の場合: other_text 必須（1〜200文字）
- selected_choice != "X" の場合: other_text は無視（保存しない）
- other_text が200文字超: 422 Validation Error

### BR-COG-08: 回答の一意性
- 1設問につき1回答のみ（UNIQUE制約）
- 回答済み設問への再回答: 409 Conflict「すでに回答済みです」

### BR-COG-09: 回答のセッション検証
- セッションステータスが `media_uploaded` であること
- セッションが自分のものであること
- 違反時: 403 Forbidden / 422 Validation Error

---

## 3. 自由記述ルール

### BR-COG-10: 自由記述任意
- 自由記述は任意入力（スキップ可能）
- 自由記述なしでも感情選択肢生成に進める

### BR-COG-11: 自由記述バリデーション
- 文字数: 1〜500文字
- 0文字（空）: 422 Validation Error「内容を入力してください」
- 500文字超: 422 Validation Error「500文字以内で入力してください」

### BR-COG-12: 自由記述の一意性
- 1セッションにつき1件のみ（session_id UNIQUE制約）
- 既存入力がある場合の再送信: 409 Conflict「すでに入力済みです」

### BR-COG-13: 自由記述のタイミング
- 全設問回答完了後のみ入力可能
- 設問が未回答の場合: 422 Validation Error「先に全設問に回答してください」

---

## 4. 感情選択肢ルール

### BR-COG-14: 感情候補生成数
- 1セッションにつき3〜5個を生成
- Bedrockレスポンスが3個未満: デフォルト感情で補完
- Bedrockレスポンスが5個超: 先頭5個のみ採用

### BR-COG-15: 感情候補生成タイミング
- POST /api/cognitive/complete-questions 呼び出し時に生成
- 生成前に全設問回答済みであることを検証
- 自由記述は任意（あれば考慮、なくても生成可能）

### BR-COG-16: 感情候補の一意性
- 1セッションにつき候補セットは1回のみ生成
- 再生成は不可

---

## 5. 感情選択ルール

### BR-COG-17: 感情選択の最低数
- 最低1つの感情を選択する必要がある
- 0件選択: 422 Validation Error「最低1つの感情を選択してください」

### BR-COG-18: 感情の複数選択
- 複数の感情を同時選択可能（上限なし）
- 同じ候補の重複選択は不可

### BR-COG-19: 感情選択のセッション検証
- セッションステータスが `questions_answered` であること
- 選択された candidate_id が全てそのセッションの EmotionCandidate であること
- 他セッションの候補ID指定: 422 Validation Error

### BR-COG-20: 感情選択の一意性
- 1セッションにつき感情選択は1回のみ
- 選択済みの場合: 409 Conflict「すでに感情を選択済みです」

---

## 6. セッションステータス遷移ルール

### BR-COG-21: ステータス遷移（2段階）
```
media_uploaded → questions_answered → emotions_selected
```

- `media_uploaded` → `questions_answered`: POST /api/cognitive/complete-questions 成功時
- `questions_answered` → `emotions_selected`: POST /api/cognitive/emotions 成功時
- 逆方向遷移は不可
- スキップ遷移は不可（必ず順序通り）

### BR-COG-22: ステータスに基づくAPI制限
| API | 許可ステータス |
|---|---|
| POST /api/cognitive/responses | media_uploaded |
| POST /api/cognitive/free-text | media_uploaded |
| POST /api/cognitive/complete-questions | media_uploaded |
| POST /api/cognitive/emotions | questions_answered |
| GET /api/cognitive/questions/{session_id} | any (read-only) |
| GET /api/cognitive/emotions/{session_id} | any (read-only) |
