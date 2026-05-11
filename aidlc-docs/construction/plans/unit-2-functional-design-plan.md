# Functional Design Plan - Unit 2: Cognitive Mapping

## ユニットコンテキスト

### 対象ストーリー
| Story ID | 名称 | Priority |
|---|---|---|
| US-4.1 | コンテクスト設問への回答 | Must Have |
| US-4.2 | 自由記述による補足入力 | Must Have |
| US-5.1 | 感情選択肢の選択 | Must Have |

### 依存関係
- **Unit 0**: GenerationSession, JWT認証ミドルウェア
- **Unit 1**: MediaFile, ImageAnalysisResult, MusicAnalysisResult（解析結果を設問生成に利用）

### 機能要件（FR参照）
- FR-3.1〜3.5: メディアコンテクスト入力（設問生成、回答、自由記述）
- FR-4.1〜4.3: 感情アノテーション（感情選択肢生成、選択）

---

## 設計対象

### Part A: ドメインエンティティ設計
- [x] ContextQuestion（AI生成された設問）
- [x] ContextResponse（ユーザー回答）
- [x] FreeTextInput（自由記述入力）
- [x] EmotionCandidate（AI生成された感情選択肢）
- [x] EmotionSelection（ユーザー選択した感情）
- [x] Entity Relationships（リレーション定義）

### Part B: ビジネスロジック設計
- [x] コンテクスト設問生成フロー（Bedrockプロンプト設計）
- [x] 設問回答受付・保存フロー
- [x] 自由記述入力受付・保存フロー
- [x] 感情選択肢生成フロー（Bedrockプロンプト設計）
- [x] 感情選択受付・保存フロー

### Part C: ビジネスルール設計
- [x] 設問・回答関連ルール
- [x] 自由記述関連ルール
- [x] 感情選択関連ルール
- [x] セッションステータス遷移ルール

---

## 質問事項

### Q1: コンテクスト設問のデータモデル
設問と回答のデータモデルをどう設計しますか？

A) **設問テーブル + 回答テーブル分離**: AI生成された設問を `context_questions` に保存し、ユーザー回答を `context_responses` に保存。設問の再利用・監査が可能。
B) **回答テーブルのみ**: 設問内容を回答レコードに埋め込み（question_text, choices, selected_answer）。テーブル数少なくシンプル。
C) **JSON一括保存**: 設問と回答を1レコードのJSONで一括保存。最もシンプルだがクエリ性が低い。

[Answer]:A

### Q2: 設問生成タイミング
コンテクスト設問はいつ生成しますか？

A) **メディア解析完了時に同期生成**: upload_and_analyze の一部として設問も生成。ユーザーの待ち時間が増えるが、解析後すぐ設問が表示される。
B) **設問取得API呼び出し時に遅延生成**: GET /api/cognitive/questions で初回アクセス時に生成・キャッシュ。アップロードレスポンスが速い。
C) **セッションステータス遷移時に生成**: media_uploaded → questions_generated のステータス遷移で生成。明示的だが別API呼び出しが必要。

[Answer]:A

### Q3: 設問回答の必須/任意
設問回答は必須ですか？

A) **全問任意**: 全問スキップ可能（US-4.1 AC5「全設問への回答は必須ではなく、スキップ可能」に準拠）。回答ゼロでも感情選択肢生成に進める。
B) **最低1問回答必須**: 感情選択肢の品質確保のため最低1問は回答が必要。
C) **全問必須**: 全問回答しないと次ステップに進めない。

[Answer]:C

### Q4: 感情選択肢のデータ構造
感情選択肢はどのように保存しますか？

A) **感情候補テーブル + 選択テーブル分離**: AI生成された候補を `emotion_candidates` に、ユーザー選択を `emotion_selections` に保存。
B) **候補と選択を1テーブル**: `emotion_candidates` テーブルに `is_selected` フラグ。テーブル数少ない。
C) **JSONで一括**: 候補リストと選択結果をセッションにJSON保存。

[Answer]:A

### Q5: 「その他」選択時の自由記述
設問の「その他」を選択した場合の自由記述はどう扱いますか？

A) **選択肢の一部として保存**: 回答レコードに `other_text` カラムを持ち、「その他」選択時のみ保存。
B) **別テーブルで管理**: 自由記述は常に `free_text_inputs` テーブルに保存（設問回答の自由記述と最終自由記述を統一管理）。
C) **回答テキストに統合**: selected_answer に「その他: {入力内容}」として保存。

[Answer]:A

### Q6: セッションステータス遷移
Unit 2 でのステータス遷移はどうしますか？

A) **2段階遷移**: `media_uploaded` → `questions_answered`（設問回答+自由記述完了時）→ `emotions_selected`（感情選択完了時）
B) **1段階遷移**: `media_uploaded` → `emotions_selected`（感情選択完了時に一括遷移）
C) **3段階遷移**: `media_uploaded` → `questions_answered` → `free_text_entered` → `emotions_selected`（各アクションで遷移）

[Answer]:A
