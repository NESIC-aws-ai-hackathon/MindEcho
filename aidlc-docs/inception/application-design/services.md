# Services - MindEcho

## サービスレイヤー設計方針
PoC規模のシンプルモジュール分割のため、明示的なサービスレイヤーは設けず、各モジュールの `logic.py` がサービスロジックを担当する。モジュール間の連携は直接importまたはセッションIDを介したDB参照で行う。

---

## SVC-01: Auth Service (`app/auth/logic.py`)
**責務**: 認証・認可のビジネスロジック

| オペレーション | 処理内容 |
|---|---|
| `register_user` | メール重複チェック → パスワードハッシュ化 → DB保存 → JWTトークン生成 |
| `authenticate_user` | メール検索 → パスワード検証 → JWTトークン生成 |
| `request_password_reset` | リセットトークン生成（24時間有効）→ メール送信 |
| `confirm_password_reset` | トークン検証 → 新パスワードハッシュ化 → DB更新 |
| `delete_account` | 全関連データ削除（Data Service連携）→ ユーザーレコード削除 |

**連携先**: Data Service（アカウント削除時の全データ削除）

---

## SVC-02: Media Analysis Service (`app/media/logic.py`)
**責務**: メディアアップロード + 解析のオーケストレーション

| オペレーション | 処理内容 |
|---|---|
| `upload_and_analyze` | バリデーション → S3アップロード → メディア種別判定 → 解析実行 → DB保存 |
| `analyze_by_type` | メディア種別に応じた解析器を選択・実行（Strategy Pattern） |

**オーケストレーションフロー**:
```
upload_and_analyze(file, media_type)
  ├─ validate_file(file, media_type)          # 形式・サイズチェック
  ├─ upload_to_s3(file) → s3_key             # S3保存
  ├─ save_media_record(s3_key, media_type)    # DB記録
  ├─ analyze_by_type(s3_key, media_type)      # 解析実行（同期）
  │   ├─ image  → image_analyzer.analyze()
  │   ├─ music  → music_analyzer.analyze()
  │   ├─ manga  → manga_analyzer.analyze()
  │   └─ novel  → novel_analyzer.analyze()
  ├─ save_analysis_result(media_id, result)   # 解析結果DB保存
  └─ return MediaUploadResponse
```

**解析器選択（Strategy Pattern）**:
```python
ANALYZERS = {
    "image": ImageAnalyzer,
    "music": MusicAnalyzer,
    "manga": MangaAnalyzer,
    "novel": NovelAnalyzer,
}
```

**連携先**: Core Module（S3クライアント、Bedrockクライアント）

---

## SVC-03: Cognitive Mapping Service (`app/cognitive/logic.py`)
**責務**: コンテクスト設問 + 感情選択肢の生成・管理

| オペレーション | 処理内容 |
|---|---|
| `generate_questions` | 解析結果取得 → Bedrockでメディア種別・メタデータに基づく設問生成 → セッション作成 |
| `save_answers` | 回答バリデーション → DB保存 |
| `generate_emotions` | 解析結果 + コンテクスト回答を統合 → Bedrockで感情選択肢生成 |
| `save_emotion_selection` | 感情選択バリデーション（1つ以上必須）→ DB保存 |

**オーケストレーションフロー**:
```
generate_questions(media_id)
  ├─ get_analysis_result(media_id)           # 解析結果取得
  ├─ create_session(media_id)                # セッションレコード作成
  ├─ build_question_prompt(analysis_result)  # プロンプト構築
  ├─ call_bedrock(prompt) → questions        # AI設問生成
  └─ return ContextQuestions

generate_emotions(session_id)
  ├─ get_analysis_result(session.media_id)   # 解析結果取得
  ├─ get_context_answers(session_id)         # コンテクスト回答取得
  ├─ build_emotion_prompt(analysis, answers) # プロンプト構築
  ├─ call_bedrock(prompt) → emotions         # AI感情選択肢生成
  └─ return EmotionChoices
```

**連携先**: Media Module（解析結果参照）、Core Module（Bedrockクライアント）

---

## SVC-04: Sentence Synthesis Service (`app/synthesis/logic.py`)
**責務**: 文章生成のオーケストレーション

| オペレーション | 処理内容 |
|---|---|
| `generate_text` | 全コンテクスト集約 → Bedrockで文章生成 → DB保存 |
| `regenerate_text` | 再生成回数チェック → 異なるバリエーション生成 → DB更新 |
| `update_text` | 編集テキストのDB更新 |

**オーケストレーションフロー**:
```
generate_text(session_id, output_format)
  ├─ get_session_context(session_id)         # セッション全データ取得
  │   ├─ analysis_result                     # 解析結果
  │   ├─ context_answers                     # コンテクスト回答
  │   ├─ free_text                           # 自由記述
  │   └─ selected_emotions                   # 選択感情
  ├─ build_generation_prompt(context, format) # プロンプト構築
  │   ├─ format = "sns"    → 140-280文字指定
  │   ├─ format = "diary"  → 300-500文字指定
  │   └─ format = "review" → 500-1000文字指定
  ├─ call_bedrock(prompt) → generated_text   # AI文章生成
  ├─ save_generation(session_id, text, format) # DB保存
  └─ return GenerateResponse (text + analysis_result_summary)
```

**連携先**: Cognitive Module（セッションデータ参照）、Media Module（解析結果参照）、Core Module（Bedrockクライアント）

---

## SVC-05: Data Management Service (`app/data/logic.py`)
**責務**: 履歴管理・データ削除・エクスポート

| オペレーション | 処理内容 |
|---|---|
| `get_history_list` | ページネーション付き生成履歴取得 |
| `get_history_detail` | 生成詳細（全コンテクスト含む）取得 |
| `delete_generation` | 生成レコード + 関連S3ファイル削除 |
| `delete_all_user_data` | ユーザーの全データ（DB + S3）一括削除 |
| `export_user_data` | 全ユーザーデータをJSON形式で集約・返却 |

**連携先**: Core Module（S3クライアント、DB）

---

## クロスカッティングサービス

### 認証ミドルウェア (`app/core/middleware.py`)
全API（`/api/auth/register`, `/api/auth/login`, `/api/auth/reset-password/*` を除く）に対してJWTトークン検証を行い、リクエストコンテキストにユーザー情報を注入する。

### エラーハンドリング (`app/core/exceptions.py`)
統一的なエラーレスポンス形式を提供:
```json
{
  "error": {
    "code": "MEDIA_TOO_LARGE",
    "message": "ファイルサイズが上限を超えています",
    "details": { "max_size_mb": 50, "actual_size_mb": 75 }
  }
}
```

---

## セッション管理モデル

メインフローの一連の操作を `generation_sessions` テーブルで管理:

```
Session Lifecycle:
  CREATED → MEDIA_UPLOADED → ANALYZED → CONTEXT_ANSWERED 
    → EMOTIONS_SELECTED → TEXT_GENERATED → COMPLETED
```

セッションIDを介して、各ステップのデータ（メディア、解析結果、コンテクスト回答、感情選択、生成テキスト）を紐付ける。
