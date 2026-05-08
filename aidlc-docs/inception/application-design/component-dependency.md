# Component Dependency - MindEcho

## 依存関係マトリクス

**行 → 列 = 「行が列に依存」**

| | Core | Auth | Media | Cognitive | Synthesis | Data |
|---|---|---|---|---|---|---|
| **Core** | — | — | — | — | — | — |
| **Auth** | ✓ | — | — | — | — | ✓ |
| **Media** | ✓ | — | — | — | — | — |
| **Cognitive** | ✓ | — | ✓(R) | — | — | — |
| **Synthesis** | ✓ | — | ✓(R) | ✓(R) | — | — |
| **Data** | ✓ | — | — | — | — | — |

- ✓ = 直接依存（import / 関数呼び出し）
- ✓(R) = 読み取り専用依存（DBからのデータ参照のみ）

---

## 依存関係の詳細

### Core Module（依存元: 全モジュール）
```
Core Module
  ├── config.py        ← 全モジュールが設定値を参照
  ├── database.py      ← 全モジュールがDBセッションを利用
  ├── middleware.py     ← FastAPIアプリケーションレベルで適用
  ├── s3_client.py     ← Media, Data が利用
  ├── bedrock_client.py ← Media, Cognitive, Synthesis が利用
  └── exceptions.py    ← 全モジュールがエラー型を利用
```

### Auth → Core, Data
- Core: DB接続、設定値、JWTシークレット
- Data: アカウント削除時に `delete_all_user_data()` を呼び出し

### Media → Core
- Core: S3クライアント（ファイルアップロード）、Bedrockクライアント（解析）、DB

### Cognitive → Core, Media(R)
- Core: Bedrockクライアント（設問・感情生成）、DB
- Media(R): `media_files` + 各解析結果テーブルからデータ読み取り（セッション経由）

### Synthesis → Core, Cognitive(R), Media(R)
- Core: Bedrockクライアント（文章生成）、DB
- Cognitive(R): `context_responses`, `emotion_selections` テーブルからデータ読み取り
- Media(R): 解析結果テーブルからデータ読み取り（AI解析リザルト表示用）

### Data → Core
- Core: DB接続、S3クライアント（ファイル削除）

---

## データフロー図

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│                                                                  │
│  LoginPage → RegisterPage → UploadPage → AnalyzingPage          │
│                                  │                               │
│                                  ▼                               │
│  ContextPage → EmotionsPage → GeneratePage → HistoryPage        │
└──────────────────────┬───────────────────────────────────────────┘
                       │ REST API (JSON)
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Core Module                              │   │
│  │  config │ database │ middleware │ s3_client │ bedrock     │   │
│  └────────────────────────┬──────────────────────────────────┘   │
│                           │                                      │
│  ┌────────┐  ┌────────────┴──┐  ┌──────────┐  ┌───────────┐   │
│  │  Auth  │  │    Media      │  │Cognitive │  │ Synthesis │   │
│  │Module  │  │   Module      │  │ Module   │  │  Module   │   │
│  │        │  │               │  │          │  │           │   │
│  │register│  │upload_analyze │  │questions │  │ generate  │   │
│  │login   │  │image_analyzer│  │answers   │  │regenerate │   │
│  │reset   │  │music_analyzer│  │emotions  │  │ update    │   │
│  │delete  │  │manga_analyzer│  │select    │  │           │   │
│  │        │  │novel_analyzer│  │          │  │           │   │
│  └───┬────┘  └──────┬───────┘  └────┬─────┘  └─────┬─────┘   │
│      │              │               │               │          │
│      │              │          read │          read  │          │
│      │              │      ┌───────┘      ┌────────┘          │
│      │              │      │              │                    │
│  ┌───▼──────────────▼──────▼──────────────▼──────────────┐    │
│  │              PostgreSQL (Amazon RDS)                    │    │
│  │                                                        │    │
│  │  users │ media_files │ image_analysis │ music_analysis │    │
│  │  generation_sessions │ context_responses                    │    │
│  │  emotion_selections │ free_text_inputs │ generated_texts  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────┐    ┌─────────────────┐                     │
│  │  Amazon S3     │    │  AWS Bedrock    │                     │
│  │  (メディア保存)│    │  (AI解析/生成)  │                     │
│  └────────────────┘    └─────────────────┘                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## ユーザージャーニーに沿ったデータフロー

```
Step 1: Upload & Analyze (同期)
  Frontend ─POST /api/media/upload──→ Media Module
    Media Module ──→ S3 (ファイル保存)
    Media Module ──→ Bedrock (解析)
    Media Module ──→ DB (media_files + *_analysis_results 保存)
    Media Module ←── MediaUploadResponse (media_id含む)
  Frontend ←── レスポンス受信、AnalyzingPage → ContextPage遷移

Step 2: Context Questions
  Frontend ─POST /api/cognitive/questions──→ Cognitive Module
    Cognitive Module ──→ DB (解析結果読み取り)
    Cognitive Module ──→ Bedrock (設問生成)
    Cognitive Module ──→ DB (session作成、questions保存)
  Frontend ←── ContextQuestions (session_id + questions)

Step 3: Context Answers
  Frontend ─POST /api/cognitive/answers──→ Cognitive Module
    Cognitive Module ──→ DB (context_responses 保存)
  Frontend ←── AnswerResponse

Step 4: Emotion Selection
  Frontend ─POST /api/cognitive/emotions──→ Cognitive Module
    Cognitive Module ──→ DB (解析結果 + context回答 読み取り)
    Cognitive Module ──→ Bedrock (感情選択肢生成)
  Frontend ←── EmotionChoices
  
  Frontend ─POST /api/cognitive/emotions/select──→ Cognitive Module
    Cognitive Module ──→ DB (emotion_selections 保存)
  Frontend ←── EmotionSelectResponse

Step 5: Text Generation
  Frontend ─POST /api/synthesis/generate──→ Synthesis Module
    Synthesis Module ──→ DB (全コンテクスト読み取り: 解析結果+回答+感情)
    Synthesis Module ──→ Bedrock (文章生成)
    Synthesis Module ──→ DB (generated_texts 保存)
  Frontend ←── GenerateResponse (text + analysis_result_summary)
```

---

## 通信パターン

| パターン | 適用箇所 | 説明 |
|---|---|---|
| **同期 REST** | 全API | Q2回答=Aに基づき、全APIを同期リクエスト-レスポンスで実装 |
| **DB参照（読み取り）** | Cognitive→Media, Synthesis→Media/Cognitive | セッションIDを介して他モジュールのデータをDBから読み取り |
| **直接関数呼び出し** | Auth→Data | アカウント削除時のデータ一括削除 |

---

## データベーススキーマ（正規化テーブル）

Q4回答=Aに基づき、メディア種別ごとに解析結果テーブルを分離:

```
users
  ├── id (PK)
  ├── email (UNIQUE)
  ├── password_hash
  ├── created_at
  └── updated_at

media_files
  ├── id (PK)
  ├── user_id (FK → users)
  ├── media_type (enum: image/music)
  ├── file_name
  ├── file_size
  ├── s3_key
  ├── created_at
  └── (one-to-one with corresponding analysis table)

image_analysis_results
  ├── id (PK)
  ├── media_id (FK → media_files, UNIQUE)
  ├── colors (text[])
  ├── composition (text)
  ├── mood (text)
  ├── subjects (text[])
  └── atmosphere (text)

music_analysis_results
  ├── id (PK)
  ├── media_id (FK → media_files, UNIQUE)
  ├── rhythm (text)
  ├── tempo (text)
  ├── mood (text)
  ├── genre (text)
  └── energy_level (text)

generation_sessions
  ├── id (PK)
  ├── user_id (FK → users)
  ├── media_id (FK → media_files)
  ├── status (enum: created/analyzed/context_answered/emotions_selected/text_generated)
  ├── created_at
  └── updated_at

context_responses
  ├── id (PK)
  ├── session_id (FK → generation_sessions)
  ├── question_id (text)
  ├── question_text (text)
  ├── selected_key (text)
  ├── other_text (text, nullable)
  └── created_at

free_text_inputs
  ├── id (PK)
  ├── session_id (FK → generation_sessions, UNIQUE)
  ├── text (text)
  └── created_at

emotion_selections
  ├── id (PK)
  ├── session_id (FK → generation_sessions)
  ├── emotion_label (text)
  ├── emotion_description (text)
  └── created_at

generated_texts
  ├── id (PK)
  ├── session_id (FK → generation_sessions)
  ├── text (text)
  ├── output_format (enum: sns/diary/review)
  ├── character_count (int)
  ├── regeneration_count (int, default 0)
  ├── created_at
  └── updated_at
```
