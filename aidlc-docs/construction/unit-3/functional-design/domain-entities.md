# Domain Entities - Unit 3: Sentence Synthesis

---

## Entity: GeneratedText

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | 生成テキスト一意識別子 |
| session_id | UUID | FK(generation_sessions.id), UNIQUE, NOT NULL | 所属セッション |
| output_format | String(20) | NOT NULL | 出力形式（sns / diary / review） |
| generated_content | Text | NOT NULL | 生成された文章本文 |
| generation_count | Integer | NOT NULL, default=1 | 生成回数（初回=1、再生成で+1） |
| created_at | DateTime(TZ) | NOT NULL, default=now | 初回生成日時 |
| updated_at | DateTime(TZ) | NOT NULL, default=now | 最終更新日時（再生成時に更新） |

### ビジネス制約
- 1セッションにつき最大1レコード（UNIQUE on session_id）
- 再生成時はレコードを上書き更新（generated_content + generation_count + updated_at）
- generation_count の上限は10（BR-SYN-06）
- output_format は再生成時に変更可能

### 出力形式 (output_format)

| 値 | 名称 | 文字数目安 | 説明 |
|---|---|---|---|
| sns | SNS投稿 | 140〜280文字 | カジュアル・短文、ハッシュタグ含む |
| diary | 日記・メモ | 300〜500文字 | 内省的・個人的なトーン |
| review | レビュー記事 | 500〜1000文字 | 構造的・分析的なトーン |

---

## Entity Relationships

```
┌────────────────────┐       ┌──────────────┐       ┌──────────────────┐
│ GenerationSession  │ 1   1 │  MediaFile   │ 1   1 │AnalysisResult    │
│   (Unit 0)         ├───────┤  (Unit 1)    ├───────┤ (Unit 1)         │
└────────┬───────────┘       └──────────────┘       └──────────────────┘
         │
         │ 1
         │
         ├──── 3..5 ──── ContextQuestion (Unit 2)
         │                     │ 1:1
         │                     └──── ContextResponse
         │
         ├──── 0..1 ──── FreeTextInput (Unit 2)
         │
         ├──── 3..5 ──── EmotionCandidate (Unit 2)
         │                     │ 0..1
         │                     └──── EmotionSelection
         │
         └──── 0..1 ──── GeneratedText (Unit 3) ◄ THIS UNIT
```

### 読み取り依存（Unit 3 → Unit 1, Unit 2）
- Unit 3 は Unit 1・Unit 2 のデータを**読み取りのみ**で使用
- Bedrock プロンプト構築時に全コンテクストを統合
