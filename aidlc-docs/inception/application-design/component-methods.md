# Component Methods - MindEcho

> **Note**: 本ドキュメントは各コンポーネントのメソッドシグネチャと入出力型を定義する。詳細なビジネスルール・バリデーションロジックは Construction Phase の Functional Design で定義する。

---

## Backend API Endpoints & Methods

### COMP-B01: Auth Module

#### `POST /api/auth/register`
```
Input:  RegisterRequest { email: str, password: str }
Output: AuthResponse { user_id: str, access_token: str, token_type: str }
Error:  409 Conflict (email already registered), 422 Validation Error
```

#### `POST /api/auth/login`
```
Input:  LoginRequest { email: str, password: str }
Output: AuthResponse { user_id: str, access_token: str, token_type: str }
Error:  401 Unauthorized
```

#### `POST /api/auth/reset-password/request`
```
Input:  ResetRequest { email: str }
Output: MessageResponse { message: str }
Error:  (always 200 for security)
```

#### `POST /api/auth/reset-password/confirm`
```
Input:  ResetConfirm { token: str, new_password: str }
Output: MessageResponse { message: str }
Error:  400 Bad Request (invalid/expired token)
```

#### `DELETE /api/auth/account`
```
Input:  (JWT auth header)
Output: MessageResponse { message: str }
Side Effect: ユーザーの全データ（DB + S3ファイル）を削除
```

---

### COMP-B03: Media Module

#### `POST /api/media/upload`
```
Input:  multipart/form-data { file: UploadFile, media_type: Optional[str] }
        ※ media_type: "image" | "music" | "manga" | "novel"（省略時は自動判定）
        ※ 小説テキスト直接入力の場合: JSON { text: str, media_type: "novel" }
Output: MediaUploadResponse {
          media_id: str,
          media_type: str,
          file_name: str,
          file_size: int,
          s3_key: str,
          preview_url: str,
          analysis: AnalysisResult  # 同期処理で解析結果も返す
        }
Error:  400 Bad Request (unsupported format, size exceeded)
        413 Payload Too Large
```
**Note**: Q2回答=A（同期処理）のため、アップロードと解析を1リクエストで同期実行

#### `GET /api/media/{media_id}`
```
Input:  media_id: str (path param)
Output: MediaDetail {
          media_id: str,
          media_type: str,
          file_name: str,
          preview_url: str,
          created_at: datetime,
          analysis_result: AnalysisResult
        }
Error:  404 Not Found
```

#### Internal: `analyze_image(s3_key: str) -> ImageAnalysisResult`
```
Output: ImageAnalysisResult {
          colors: list[str],
          composition: str,
          mood: str,
          subjects: list[str],
          atmosphere: str
        }
```

#### Internal: `analyze_music(s3_key: str) -> MusicAnalysisResult`
```
Output: MusicAnalysisResult {
          rhythm: str,
          tempo: str,
          mood: str,
          genre: str,
          energy_level: str
        }
```

#### Internal: `analyze_manga(s3_key: str) -> MangaAnalysisResult`
```
Output: MangaAnalysisResult {
          panel_composition: str,
          art_style: str,
          character_emotions: list[str],
          story_mood: str,
          visual_impact: str
        }
```

#### Internal: `analyze_novel(text: str) -> NovelAnalysisResult`
```
Output: NovelAnalysisResult {
          writing_style: str,
          themes: list[str],
          tone: str,
          emotional_keywords: list[str],
          narrative_mood: str
        }
```

---

### COMP-B04: Cognitive Module

#### `POST /api/cognitive/questions`
```
Input:  QuestionRequest { media_id: str }
Output: ContextQuestions {
          session_id: str,
          questions: list[Question {
            question_id: str,
            text: str,
            options: list[Option { key: str, label: str }]
          }]
        }
Error:  404 Not Found (media_id not found)
```

#### `POST /api/cognitive/answers`
```
Input:  AnswerRequest {
          session_id: str,
          answers: list[Answer { question_id: str, selected_key: str, other_text: Optional[str] }],
          free_text: Optional[str]
        }
Output: AnswerResponse { session_id: str, status: str }
Error:  422 Validation Error
```

#### `POST /api/cognitive/emotions`
```
Input:  EmotionRequest { session_id: str }
Output: EmotionChoices {
          session_id: str,
          emotions: list[Emotion { emotion_id: str, label: str, description: str }]
        }
Error:  400 Bad Request (context answers not yet submitted)
```

#### `POST /api/cognitive/emotions/select`
```
Input:  EmotionSelectRequest {
          session_id: str,
          selected_emotion_ids: list[str]  # 1つ以上必須
        }
Output: EmotionSelectResponse { session_id: str, status: str }
Error:  422 Validation Error (empty selection)
```

---

### COMP-B05: Synthesis Module

#### `POST /api/synthesis/generate`
```
Input:  GenerateRequest {
          session_id: str,
          output_format: str  # "sns" | "diary" | "review"
        }
Output: GenerateResponse {
          generation_id: str,
          session_id: str,
          text: str,
          output_format: str,
          character_count: int,
          analysis_result_summary: AnalysisResult  # AI解析リザルト（おまけ表示用）
        }
Error:  400 Bad Request (emotions not yet selected)
```

#### `POST /api/synthesis/regenerate`
```
Input:  RegenerateRequest { generation_id: str }
Output: GenerateResponse { ... }  # 同上
Error:  429 Too Many Requests (10回/セッション超過)
```

#### `PUT /api/synthesis/{generation_id}`
```
Input:  UpdateTextRequest { text: str }
Output: GenerateResponse { ... }
Error:  404 Not Found
```

---

### COMP-B06: Data Module

#### `GET /api/data/history`
```
Input:  Query params: page: int = 1, per_page: int = 20
Output: HistoryList {
          items: list[HistoryItem {
            generation_id: str,
            media_type: str,
            output_format: str,
            text_preview: str,
            created_at: datetime
          }],
          total: int,
          page: int,
          per_page: int
        }
```

#### `GET /api/data/history/{generation_id}`
```
Input:  generation_id: str (path param)
Output: HistoryDetail {
          generation_id: str,
          text: str,
          output_format: str,
          media_preview_url: str,
          media_type: str,
          selected_emotions: list[str],
          context_answers: list[ContextAnswer],
          analysis_result: AnalysisResult,
          created_at: datetime
        }
```

#### `DELETE /api/data/history/{generation_id}`
```
Input:  generation_id: str (path param)
Output: MessageResponse { message: str }
Side Effect: 関連メディアファイル(S3)も削除
```

#### `DELETE /api/data/history`
```
Input:  (JWT auth header, no body)
Output: MessageResponse { message: str, deleted_count: int }
Side Effect: ユーザーの全履歴 + 全S3ファイルを削除
```

#### `GET /api/data/export`
```
Input:  (JWT auth header)
Output: application/json ファイルダウンロード
        ExportData {
          user: { email: str, created_at: datetime },
          generations: list[HistoryDetail],
          media_files: list[MediaFileMeta]
        }
```

---

## Frontend Page Methods

### 各ページの主要メソッド

| ページ | メソッド | 説明 |
|---|---|---|
| LoginPage | `handleLogin(email, password)` | ログインAPI呼び出し、トークン保存 |
| RegisterPage | `handleRegister(email, password)` | 登録API呼び出し、自動ログイン |
| UploadPage | `handleUpload(file, mediaType)` | メディアアップロード+解析API呼び出し |
| UploadPage | `handleTextInput(text)` | 小説テキスト直接入力 |
| ContextPage | `loadQuestions(mediaId)` | コンテクスト設問取得 |
| ContextPage | `submitAnswers(answers, freeText)` | 回答送信 |
| EmotionsPage | `loadEmotions(sessionId)` | 感情選択肢取得 |
| EmotionsPage | `selectEmotions(emotionIds)` | 感情選択送信 |
| GeneratePage | `generate(sessionId, format)` | 文章生成API呼び出し |
| GeneratePage | `regenerate(generationId)` | 再生成API呼び出し |
| GeneratePage | `copyToClipboard(text)` | クリップボードコピー |
| GeneratePage | `shareToSNS(text, platform)` | Web Intent/Share API呼び出し |
| HistoryPage | `loadHistory(page)` | 履歴一覧取得 |
| HistoryPage | `deleteItem(generationId)` | 個別削除 |
| HistoryPage | `exportData()` | データエクスポート |
| SettingsPage | `deleteAllData()` | 全データ一括削除 |
| SettingsPage | `deleteAccount()` | アカウント削除 |
