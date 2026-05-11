# Domain Entities - Unit 2: Cognitive Mapping

---

## Entity: ContextQuestion

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | 設問一意識別子 |
| session_id | UUID | FK(generation_sessions.id), NOT NULL | 所属セッション |
| question_order | Integer | NOT NULL | 表示順（1-based） |
| question_text | String(500) | NOT NULL | 設問本文 |
| choices | JSON (list[dict]) | NOT NULL | 選択肢リスト [{label: "A", text: "..."}, ...] |
| created_at | DateTime(TZ) | NOT NULL, default=now | 生成日時 |

### 選択肢構造 (choices JSON)
```json
[
  {"label": "A", "text": "日常風景"},
  {"label": "B", "text": "旅行先"},
  {"label": "C", "text": "アート作品"},
  {"label": "D", "text": "思い出の一枚"},
  {"label": "X", "text": "その他"}
]
```

### ビジネス制約
- 1セッションにつき3〜5問生成
- メディア解析完了時（upload_and_analyze内）に同期生成
- 各設問には4〜5選択肢 + 「その他(X)」の構成

---

## Entity: ContextResponse

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | 回答一意識別子 |
| question_id | UUID | FK(context_questions.id), UNIQUE, NOT NULL | 対象設問 |
| session_id | UUID | FK(generation_sessions.id), NOT NULL | 所属セッション |
| selected_choice | String(10) | NOT NULL | 選択されたラベル（A/B/C/D/X） |
| other_text | String(200) | NULL | 「その他」選択時の自由記述 |
| created_at | DateTime(TZ) | NOT NULL, default=now | 回答日時 |

### ビジネス制約
- 1設問につき1回答（1:1）
- 全問回答必須（全ContextQuestionに対してContextResponseが必要）
- selected_choice が "X" の場合のみ other_text に値を持つ
- other_text の最大文字数: 200文字

---

## Entity: FreeTextInput

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | 自由記述一意識別子 |
| session_id | UUID | FK(generation_sessions.id), UNIQUE, NOT NULL | 所属セッション |
| content | String(500) | NOT NULL | 自由記述テキスト |
| created_at | DateTime(TZ) | NOT NULL, default=now | 入力日時 |

### ビジネス制約
- 1セッションにつき最大1件
- 任意入力（スキップ可能）
- 最大500文字
- 設問回答完了後にのみ入力可能

---

## Entity: EmotionCandidate

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | 感情候補一意識別子 |
| session_id | UUID | FK(generation_sessions.id), NOT NULL | 所属セッション |
| candidate_order | Integer | NOT NULL | 表示順（1-based） |
| emotion_label | String(100) | NOT NULL | 感情ラベル（例: 「懐かしさ」「安らぎ」） |
| emotion_description | String(300) | NOT NULL | 感情の説明文 |
| created_at | DateTime(TZ) | NOT NULL, default=now | 生成日時 |

### ビジネス制約
- 1セッションにつき3〜5個生成
- メディア解析結果 + コンテクスト回答 + 自由記述を基にAI生成
- 設問回答完了後（+ 自由記述入力後）に生成

---

## Entity: EmotionSelection

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | 選択一意識別子 |
| candidate_id | UUID | FK(emotion_candidates.id), NOT NULL | 選択した候補 |
| session_id | UUID | FK(generation_sessions.id), NOT NULL | 所属セッション |
| created_at | DateTime(TZ) | NOT NULL, default=now | 選択日時 |

### ビジネス制約
- 複数選択可能（1〜N件）
- 最低1つの感情が選択必須
- 同じ候補の重複選択不可（candidate_id + session_id でUNIQUE）

---

## Entity Relationships

```
┌────────────────────┐       ┌──────────────┐       ┌──────────────────┐
│ GenerationSession  │ 1   1 │  MediaFile   │ 1   1 │AnalysisResult    │
│   (Unit 0)         ├───────►│  (Unit 1)    ├───────►│ (Unit 1)         │
└────────┬───────────┘       └──────────────┘       └──────────────────┘
         │
         │ 1
         ├────────────────────────────────────────────────────────┐
         │                          │                             │
         ▼ 3..5                     ▼ 0..1                       ▼ 3..5
┌─────────────────┐      ┌──────────────────┐        ┌───────────────────┐
│ ContextQuestion │      │  FreeTextInput   │        │ EmotionCandidate  │
│                 │      │                  │        │                   │
│ session_id (FK) │      │ session_id(FK,UQ)│        │ session_id (FK)   │
└────────┬────────┘      └──────────────────┘        └────────┬──────────┘
         │                                                     │
         ▼ 1                                                   ▼ 0..1
┌─────────────────┐                                  ┌───────────────────┐
│ ContextResponse │                                  │ EmotionSelection  │
│                 │                                  │                   │
│ question_id(FK,UQ)│                                │ candidate_id (FK) │
└─────────────────┘                                  └───────────────────┘
```

### リレーション一覧

| 親 | 子 | カーディナリティ | 削除時 |
|---|---|---|---|
| GenerationSession | ContextQuestion | 1:3..5 | CASCADE |
| ContextQuestion | ContextResponse | 1:0..1 | CASCADE |
| GenerationSession | FreeTextInput | 1:0..1 | CASCADE |
| GenerationSession | EmotionCandidate | 1:3..5 | CASCADE |
| EmotionCandidate | EmotionSelection | 1:0..1 | CASCADE |
