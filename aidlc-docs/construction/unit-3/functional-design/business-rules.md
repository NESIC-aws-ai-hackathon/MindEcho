# Business Rules - Unit 3: Sentence Synthesis

---

## 1. 出力形式ルール

### BR-SYN-01: 出力形式の種類
- 3種類の出力形式を提供: sns, diary, review
- 各形式には名称・説明・文字数目安が定義されている

### BR-SYN-02: 出力形式の選択
- 生成リクエスト時に output_format パラメータで指定
- 有効値: "sns", "diary", "review"
- 無効値の場合: 422 ValidationError

### BR-SYN-03: デフォルト出力形式
- デフォルトは "sns"（フロントエンド側で初期選択）
- バックエンドでは output_format は必須パラメータ

### BR-SYN-04: 出力形式ごとの文字数目安
| 形式 | 最小文字数 | 最大文字数 |
|---|---|---|
| sns | 140 | 280 |
| diary | 300 | 500 |
| review | 500 | 1000 |

- 文字数制御はプロンプト内で指定（AI任せ）
- バックエンド側でのバリデーションは行わない
- 目安であり厳密な制約ではない

---

## 2. 文章生成ルール

### BR-SYN-05: 生成前提条件
- セッションステータスが `emotions_selected` または `generated` であること
- ユーザーがセッションの所有者であること
- 感情選択が完了していること（EmotionSelection が1つ以上存在）

### BR-SYN-06: 再生成回数制限
- セッションあたり最大10回まで生成可能（初回含む）
- generation_count が 10 に達した場合: 422 ValidationError「再生成回数の上限に達しました」
- 再生成回数は GeneratedText.generation_count で管理

### BR-SYN-07: 生成失敗時の挙動
- Bedrock API 呼び出し失敗時: エラーレスポンスを返却
- 失敗した生成は再生成回数にカウントしない
- 既存の GeneratedText レコードは変更しない（初回失敗時はレコード未作成）

### BR-SYN-08: 再生成時のテキスト保持
- 再生成時は既存レコードを上書き更新
- 過去の生成結果は保持しない（最新のみ）
- 前回とは異なる文章が生成される（Bedrock の非決定性による）

### BR-SYN-09: 再生成時の形式変更
- 再生成時に output_format を変更可能
- 変更時は新しい形式に応じたプロンプトで再生成

---

## 3. セッションステータスルール

### BR-SYN-10: ステータス遷移
- 初回生成成功時: `emotions_selected` → `generated`
- 再生成時: `generated` のまま変更なし
- 生成失敗時: ステータス変更なし

### BR-SYN-11: ステータスによるAPI許可
| API | emotions_selected | generated | その他 |
|---|---|---|---|
| POST /generate | ✅ (初回) | ✅ (再生成) | ❌ |
| GET /{session_id} | ❌ (未生成) | ✅ | ❌ |
| GET /formats | ✅ | ✅ | ✅ (認証不要) |

---

## 4. コンテクスト統合ルール

### BR-SYN-12: コンテクスト必須要素
- メディア解析結果（ImageAnalysisResult または MusicAnalysisResult）: 必須
- コンテクスト回答（ContextResponse）: 必須（全問回答済み前提）
- 感情選択（EmotionSelection + EmotionCandidate）: 必須（1つ以上）

### BR-SYN-13: コンテクスト任意要素
- FreeTextInput: 任意（存在しない場合は「入力なし」としてプロンプトに含める）

### BR-SYN-14: プロンプト構築
- 出力形式ごとに異なるプロンプトテンプレートを使用
- 共通コンテクスト（解析結果 + 回答 + 自由記述 + 感情）は全形式で同一
- プロンプトはテキストのみ出力を指示（説明・前置き不要）

---

## 5. APIルール

### BR-SYN-15: 生成レスポンス
- 生成成功時: 201 Created
- レスポンスボディ: generated_content, output_format, generation_count, session_id

### BR-SYN-16: 取得レスポンス
- 取得成功時: 200 OK
- 生成テキスト未存在時: 404 NotFound

### BR-SYN-17: 形式一覧レスポンス
- 認証不要の静的レスポンス
- 200 OK

### BR-SYN-18: エラーレスポンス
- 権限エラー: 403 Forbidden
- 未存在: 404 NotFound
- ステータス不正 / バリデーションエラー: 422 Unprocessable Entity
