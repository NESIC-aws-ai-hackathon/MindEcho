# Code Generation Plan - Unit 2: Cognitive Mapping

## ユニットコンテキスト

### 対象ストーリー
| Story ID | 名称 | 実装内容 |
|---|---|---|
| US-4.1 | コンテクスト設問への回答 | 設問生成 + 回答API |
| US-4.2 | 自由記述による補足入力 | 自由記述API |
| US-5.1 | 感情選択肢の選択 | 感情候補生成 + 選択API |

### 依存関係
- **Unit 0 への依存**: Core モジュール（database, middleware, exceptions）、GenerationSession
- **Unit 1 への依存**: MediaFile, ImageAnalysisResult, MusicAnalysisResult（設問生成の入力）
- **Unit 1 への変更**: upload_and_analyze に設問生成呼び出しを追加

### インターフェース
- `POST /api/cognitive/responses` — 設問回答一括送信
- `POST /api/cognitive/free-text` — 自由記述入力
- `POST /api/cognitive/complete-questions` — 設問回答完了 + 感情候補生成
- `POST /api/cognitive/emotions` — 感情選択送信
- `GET /api/cognitive/questions/{session_id}` — 設問取得
- `GET /api/cognitive/emotions/{session_id}` — 感情候補取得

### データベースエンティティ
- **ContextQuestion** — AI生成設問
- **ContextResponse** — ユーザー回答
- **FreeTextInput** — 自由記述
- **EmotionCandidate** — AI生成感情候補
- **EmotionSelection** — ユーザー感情選択

### 生成先パス
- **アプリケーションコード**: `backend/app/cognitive/`
- **テスト**: `backend/tests/`
- **マイグレーション**: `backend/alembic/versions/`
- **ドキュメント**: `aidlc-docs/construction/unit-2/code/`

---

## 実行ステップ

### Step 1: Cognitive モジュール — モデル定義
- [x] `backend/app/cognitive/__init__.py`
- [x] `backend/app/cognitive/models.py`
  - ContextQuestion SQLAlchemy モデル（6属性）
  - ContextResponse SQLAlchemy モデル（6属性）
  - FreeTextInput SQLAlchemy モデル（4属性）
  - EmotionCandidate SQLAlchemy モデル（6属性）
  - EmotionSelection SQLAlchemy モデル（4属性）
  - Pydantic スキーマ:
    - ContextQuestionSchema / ContextResponseSchema
    - SubmitResponsesRequest / FreeTextRequest
    - EmotionCandidateSchema / SelectEmotionsRequest
    - QuestionsResponse / EmotionsResponse

### Step 2: Cognitive モジュール — 設問生成ロジック
- [x] `backend/app/cognitive/question_generator.py`
  - generate_questions(session_id, media_file, analysis_result) → list[ContextQuestion]
  - 画像/音楽別 Bedrock プロンプト構築
  - レスポンスパース（JSON抽出 + フォールバック3問）
  - ContextQuestion レコード保存

### Step 3: Cognitive モジュール — 感情生成ロジック
- [x] `backend/app/cognitive/emotion_generator.py`
  - generate_emotions(session_id, analysis, responses, free_text) → list[EmotionCandidate]
  - Bedrock プロンプト構築（解析結果 + 回答 + 自由記述）
  - レスポンスパース（JSON抽出 + フォールバック5感情）
  - EmotionCandidate レコード保存

### Step 4: Cognitive モジュール — ビジネスロジック
- [x] `backend/app/cognitive/logic.py`
  - submit_responses(session_id, user_id, responses) — 全問回答受付
  - submit_free_text(session_id, user_id, content) — 自由記述保存
  - complete_questions(session_id, user_id) — 回答完了 + 感情生成 + ステータス遷移
  - select_emotions(session_id, user_id, candidate_ids) — 感情選択 + ステータス遷移
  - get_questions(session_id, user_id) — 設問取得（回答付き）
  - get_emotions(session_id, user_id) — 感情候補取得（選択付き）

### Step 5: Cognitive モジュール — APIルーター
- [x] `backend/app/cognitive/router.py`
  - POST /api/cognitive/responses → 201
  - POST /api/cognitive/free-text → 201
  - POST /api/cognitive/complete-questions → 201
  - POST /api/cognitive/emotions → 201
  - GET /api/cognitive/questions/{session_id} → 200
  - GET /api/cognitive/emotions/{session_id} → 200
  - 全エンドポイントに JWT 認証必須

### Step 6: Unit 1 統合 — 設問生成の組み込み
- [x] `backend/app/media/logic.py` 修正
  - upload_and_analyze 成功後に question_generator.generate_questions() を呼び出し
  - 設問生成失敗時もアップロード自体は成功扱い（try/except）

### Step 7: ユニットテスト — 生成ロジック
- [x] `backend/tests/test_question_generator.py`
  - Bedrockレスポンスのパーステスト（正常JSON）
  - パース失敗時フォールバック3問テスト
  - 設問数制限テスト（3〜5問）
  - 画像/音楽別プロンプト構築テスト
- [x] `backend/tests/test_emotion_generator.py`
  - Bedrockレスポンスのパーステスト
  - パース失敗時フォールバック5感情テスト
  - 候補数制限テスト（3〜5個）

### Step 8: ユニットテスト — ロジック & API
- [x] `backend/tests/test_cognitive_logic.py`
  - 回答送信正常系/全問未回答エラー
  - 自由記述正常系/重複エラー
  - complete-questions正常系/ステータス遷移検証
  - 感情選択正常系/最低1つ検証
- [x] `backend/tests/test_cognitive_router.py`
  - 全6エンドポイントの正常系/認証/権限テスト
  - ステータス不正時の422テスト

### Step 9: データベースマイグレーション
- [x] `backend/alembic/versions/003_cognitive_tables.py`
  - context_questions テーブル
  - context_responses テーブル
  - free_text_inputs テーブル
  - emotion_candidates テーブル
  - emotion_selections テーブル
  - FK制約 + UNIQUE制約 + インデックス

### Step 10: main.py 統合
- [x] `backend/app/main.py` に cognitive router を登録

### Step 11: ドキュメント生成
- [x] `aidlc-docs/construction/unit-2/code/code-summary.md`
  - 生成ファイル一覧
  - APIエンドポイント仕様
  - テスト一覧

---

## ストーリートレーサビリティ

| Story ID | 実装ステップ | 完了条件 |
|---|---|---|
| US-4.1 | Step 1〜6, 9 | 設問生成 + 回答受付が動作 |
| US-4.2 | Step 1, 4, 5, 9 | 自由記述入力が動作 |
| US-5.1 | Step 1, 3〜5, 9 | 感情候補生成 + 選択が動作 |

---

## 合計スコープ
- **ソースファイル**: 6ファイル（models, question_generator, emotion_generator, logic, router, __init__）
- **既存ファイル修正**: 2ファイル（media/logic.py, main.py）
- **テストファイル**: 4ファイル
- **マイグレーション**: 1ファイル
- **ドキュメント**: 1ファイル
