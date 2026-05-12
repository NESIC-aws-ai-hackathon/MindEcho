# Code Generation Plan - Unit 3: Sentence Synthesis

## ユニットコンテキスト

### 対象ストーリー
| Story ID | 名称 | 実装内容 |
|---|---|---|
| US-6.1 | 出力形式の選択 | 形式一覧API + 生成時パラメータ |
| US-6.2 | 文章生成と結果表示 | 全コンテクスト統合 → Bedrock 生成 |
| US-6.4 | 文章の再生成 | 同一エンドポイント、上書き更新、10回制限 |

### 依存関係
- **Unit 0**: Core モジュール（database, bedrock_client, middleware, exceptions）
- **Unit 1**: MediaFile, ImageAnalysisResult, MusicAnalysisResult（読み取り）
- **Unit 2**: ContextQuestion, ContextResponse, FreeTextInput, EmotionCandidate, EmotionSelection（読み取り）

### インターフェース
- `POST /api/synthesis/generate` — 文章生成（初回 + 再生成）
- `GET /api/synthesis/{session_id}` — 生成テキスト取得
- `GET /api/synthesis/formats` — 出力形式一覧

### 生成先パス
- **アプリケーションコード**: `backend/app/synthesis/`
- **テスト**: `backend/tests/`
- **マイグレーション**: `backend/alembic/versions/`
- **ドキュメント**: `aidlc-docs/construction/unit-3/code/`

---

## 実行ステップ

### Step 1: Synthesis モジュール — モデル定義
- [x] `backend/app/synthesis/__init__.py`
- [x] `backend/app/synthesis/models.py`
  - GeneratedText SQLAlchemy モデル（7属性）
  - OutputFormat enum（sns, diary, review）
  - Pydantic スキーマ:
    - GenerateRequest（session_id, output_format）
    - GeneratedTextSchema（レスポンス）
    - FormatInfo / FormatsResponse

### Step 2: Synthesis モジュール — テキスト生成ロジック
- [x] `backend/app/synthesis/text_generator.py`
  - build_common_context(analysis, responses, questions, free_text, emotions)
  - build_prompt(output_format, common_context) — 3形式別テンプレート
  - generate_text(prompt) → str — Bedrock呼び出し

### Step 3: Synthesis モジュール — ビジネスロジック
- [x] `backend/app/synthesis/logic.py`
  - generate_or_regenerate(session_id, user_id, output_format) — 生成/再生成統合
  - get_generated_text(session_id, user_id) — 取得
  - get_formats() — 静的データ返却

### Step 4: Synthesis モジュール — APIルーター
- [x] `backend/app/synthesis/router.py`
  - POST /api/synthesis/generate → 201
  - GET /api/synthesis/formats → 200（認証不要）
  - GET /api/synthesis/{session_id} → 200

### Step 5: ユニットテスト — 生成ロジック
- [x] `backend/tests/test_text_generator.py`
  - コンテクスト構築テスト（画像/音楽）
  - 形式別プロンプト構築テスト（sns/diary/review）

### Step 6: ユニットテスト — ロジック & API
- [x] `backend/tests/test_synthesis_logic.py`
  - 初回生成正常系/ステータス遷移検証
  - 再生成正常系/generation_count 増加
  - 再生成10回上限エラー
  - ステータス不正エラー
  - 取得正常系/404テスト
- [x] `backend/tests/test_synthesis_router.py`
  - 全3エンドポイント正常系
  - 認証/権限テスト
  - formats認証不要テスト

### Step 7: データベースマイグレーション
- [x] `backend/alembic/versions/004_synthesis_tables.py`
  - generated_texts テーブル
  - FK制約 + UNIQUE制約

### Step 8: main.py 統合
- [x] `backend/app/main.py` に synthesis router を登録

### Step 9: ドキュメント生成
- [x] `aidlc-docs/construction/unit-3/code/code-summary.md`

---

## ストーリートレーサビリティ

| Story ID | 実装ステップ | 完了条件 |
|---|---|---|
| US-6.1 | Step 1, 3, 4 | 形式一覧取得 + 生成時形式指定 |
| US-6.2 | Step 1〜4, 7 | 全コンテクスト統合 → 文章生成 → 取得 |
| US-6.4 | Step 1, 3, 4 | 再生成（上書き、10回制限、形式変更可） |

---

## 合計スコープ
- **ソースファイル**: 5ファイル（models, text_generator, logic, router, __init__）
- **既存ファイル修正**: 1ファイル（main.py）
- **テストファイル**: 3ファイル
- **マイグレーション**: 1ファイル
- **ドキュメント**: 1ファイル
