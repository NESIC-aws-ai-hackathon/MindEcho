# Functional Design Plan - Unit 3: Sentence Synthesis

## ユニットコンテキスト

### 対象ストーリー
| Story ID | 名称 | Priority |
|---|---|---|
| US-6.1 | 出力形式の選択 | Must Have |
| US-6.2 | 文章生成と結果表示 | Must Have |
| US-6.4 | 文章の再生成 | Must Have |

**除外**: US-6.3 (文章の編集) は DEFERRED

### ユニット責務
- 全コンテクスト（解析結果 + コンテクスト回答 + 感情選択）を統合した文章生成
- 出力形式制御（SNS / 日記 / レビュー）
- 再生成（セッションあたり10回制限）

### 依存関係
- Unit 0: Core (DB, Bedrock client, Auth)
- Unit 1: MediaFile, ImageAnalysisResult, MusicAnalysisResult (読み取り)
- Unit 2: ContextQuestion, ContextResponse, FreeTextInput, EmotionCandidate, EmotionSelection (読み取り)

---

## 設計ステップ

- [x] Step 1: ドメインエンティティ定義 (GeneratedText)
- [x] Step 2: ビジネスロジックモデル（文章生成フロー、再生成フロー）
- [x] Step 3: Bedrock プロンプト設計（3形式: SNS/日記/レビュー）
- [x] Step 4: ビジネスルール定義
- [x] Step 5: アーティファクト生成

---

## コンテキスト質問

### Q1: 出力形式の選択タイミング
出力形式の選択はどのタイミングで行いますか？

A) 感情選択後、生成リクエスト時にパラメータとして渡す（1 APIで完結）
B) 感情選択後に別エンドポイントで形式を事前選択・保存し、その後に生成リクエスト

[Answer]: A

### Q2: 生成テキストの保存モデル
再生成時に過去の生成結果をどう扱いますか？

A) 最新のみ保持（1レコード上書き方式: generated_texts に1行、再生成で内容更新）
B) 全生成履歴保持（各生成を別レコードとして保存し、表示は最新のみ）
C) 最新のみ保持（過去の生成は物理削除して最新1件のみ）

[Answer]: A

### Q3: セッションステータス遷移
文章生成完了時のセッションステータスをどうしますか？

A) `emotions_selected` → `generated`（生成完了で遷移、再生成しても `generated` のまま）
B) `emotions_selected` → `generated` → `completed`（生成後にユーザーが明示的に「完了」する）

[Answer]: A

### Q4: 生成失敗時の挙動
Bedrock API 呼び出しが失敗した場合の挙動は？

A) エラーレスポンス返却のみ（再生成回数はカウントしない）
B) エラーレスポンス返却 + 再生成回数をカウント

[Answer]: A

### Q5: 出力形式ごとの文字数制御
文字数範囲（SNS: 140-280, 日記: 300-500, レビュー: 500-1000）はどう制御しますか？

A) プロンプト内で文字数指定（AI任せ、超過・不足時はそのまま返す）
B) プロンプト内で文字数指定 + 生成後にバリデーション（範囲外なら自動リトライ1回）
C) プロンプト内で文字数指定 + バリデーションし、範囲外ならエラーとして再生成を促す

[Answer]: A

### Q6: AI解析リザルトの表示内容
US-6.2 AC5「AI解析リザルトとしてメディア解析結果をおまけ表示」の範囲は？

A) 生成APIレスポンスに解析結果サマリーを含める（バックエンドが整形）
B) フロントエンドが別途 GET /api/media/{id} で取得して表示（バックエンド変更不要）

[Answer]: B
