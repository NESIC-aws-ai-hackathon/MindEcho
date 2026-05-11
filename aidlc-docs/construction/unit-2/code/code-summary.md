# Code Summary - Unit 2: Cognitive Mapping

## 生成ファイル一覧

| # | ファイル | 種別 | 説明 |
|---|---|---|---|
| 1 | `backend/app/cognitive/__init__.py` | ソース | モジュール初期化 |
| 2 | `backend/app/cognitive/models.py` | ソース | SQLAlchemy モデル5つ + Pydantic スキーマ |
| 3 | `backend/app/cognitive/question_generator.py` | ソース | Bedrock設問生成 + フォールバック |
| 4 | `backend/app/cognitive/emotion_generator.py` | ソース | Bedrock感情生成 + フォールバック |
| 5 | `backend/app/cognitive/logic.py` | ソース | ビジネスロジック6関数 |
| 6 | `backend/app/cognitive/router.py` | ソース | FastAPI ルーター6エンドポイント |
| 7 | `backend/app/media/logic.py` | 修正 | 設問生成呼び出し追加 |
| 8 | `backend/app/main.py` | 修正 | cognitive router 登録 |
| 9 | `backend/tests/test_question_generator.py` | テスト | 設問生成ユニットテスト |
| 10 | `backend/tests/test_emotion_generator.py` | テスト | 感情生成ユニットテスト |
| 11 | `backend/tests/test_cognitive_logic.py` | テスト | ロジック層テスト |
| 12 | `backend/tests/test_cognitive_router.py` | テスト | API統合テスト |
| 13 | `backend/alembic/versions/003_cognitive_tables.py` | マイグレーション | 5テーブル作成 |

## APIエンドポイント

| メソッド | パス | 説明 | ステータス |
|---|---|---|---|
| POST | `/api/cognitive/responses` | 設問回答一括送信 | 201 |
| POST | `/api/cognitive/free-text` | 自由記述入力 | 201 |
| POST | `/api/cognitive/complete-questions` | 回答完了 + 感情候補生成 | 201 |
| POST | `/api/cognitive/emotions` | 感情選択送信 | 201 |
| GET | `/api/cognitive/questions/{session_id}` | 設問取得（回答付き） | 200 |
| GET | `/api/cognitive/emotions/{session_id}` | 感情候補取得（選択付き） | 200 |

## データモデル

### テーブル
- **context_questions** — AI生成設問（3〜5問/セッション）
- **context_responses** — ユーザー回答（設問と1:1）
- **free_text_inputs** — 自由記述（0〜1件/セッション）
- **emotion_candidates** — AI生成感情候補（3〜5個/セッション）
- **emotion_selections** — ユーザー感情選択（1〜N件）

### ステータス遷移
```
media_uploaded → (回答送信) → media_uploaded
               → (complete-questions) → questions_answered
               → (感情選択) → emotions_selected
```

## テスト一覧

| ファイル | テストクラス | テスト数 |
|---|---|---|
| test_question_generator.py | TestExtractJson, TestParseQuestions, TestBuildImagePrompt, TestBuildMusicPrompt, TestDefaultQuestions | 15 |
| test_emotion_generator.py | TestExtractJson, TestParseEmotions, TestBuildAnalysisSummary, TestBuildResponsesSummary, TestDefaultEmotions | 14 |
| test_cognitive_logic.py | TestSubmitResponses, TestSubmitFreeText, TestCompleteQuestions, TestSelectEmotions, TestGetQuestions, TestGetEmotions | 13 |
| test_cognitive_router.py | TestPostResponses, TestPostFreeText, TestPostCompleteQuestions, TestPostEmotions, TestGetQuestions, TestGetEmotions | 11 |

## ストーリー実装状況

| Story | 状態 | 実装内容 |
|---|---|---|
| US-4.1 | ✅ 完了 | 設問生成（upload時同期）+ 回答受付 + 完了処理 |
| US-4.2 | ✅ 完了 | 自由記述入力（任意、500文字、1回限り） |
| US-5.1 | ✅ 完了 | 感情候補生成 + 複数選択（最低1つ必須） |
