# Functional Design Plan - Unit 0: Auth & Core Infrastructure

## 対象ストーリー（MVP）
| Story ID | 名称 | Priority |
|---|---|---|
| US-1.1 | ユーザー登録 | Must Have |
| US-1.2 | ログイン | Must Have |
| US-7.2 | データの削除 | Must Have |
| US-7.4 | アカウント削除 | Must Have |

**DEFERRED**: US-1.3（パスワードリセット）、US-7.1（生成履歴の閲覧）、US-7.3（データエクスポート）

---

## 実行計画

### Part A: ドメインエンティティ設計
- [x] A1. `User` エンティティの属性・制約定義
- [x] A2. `GenerationSession` エンティティの属性・ライフサイクル定義
- [x] A3. エンティティ間リレーション定義

### Part B: 認証ビジネスロジック
- [x] B1. ユーザー登録フロー（バリデーション、パスワードハッシュ化、トークン発行）
- [x] B2. ログインフロー（認証、トークン発行、エラーハンドリング）
- [x] B3. JWT トークン管理（発行、検証、有効期限）
- [x] B4. アカウント削除フロー（全データカスケード削除）

### Part C: データ管理ビジネスロジック
- [x] C1. データ削除フロー（個別セッション削除、S3ファイル連動）
- [x] C2. ユーザーデータ一括削除ロジック（アカウント削除連動）

### Part D: 共通基盤ビジネスルール
- [x] D1. 認証ミドルウェアのルール（トークン検証、エラーレスポンス）
- [x] D2. 共通バリデーションルール（メール形式、パスワード要件）
- [x] D3. エラーハンドリング方針（エラーコード体系）

### Part E: 質問収集・回答分析
- [x] E1. 質問ファイル作成・ユーザー回答収集
- [x] E2. 回答分析・曖昧性確認

### Part F: 成果物生成
- [x] F1. `domain-entities.md` 作成
- [x] F2. `business-logic-model.md` 作成
- [x] F3. `business-rules.md` 作成

---

## 質問ファイル
以下の質問に回答してください。回答は各質問の `[Answer]:` タグの後に記入してください。

---

## Question 1
JWTアクセストークンの有効期限はどの程度にしますか？

A) 15分（セキュリティ重視）
B) 1時間（標準的）
C) 24時間（PoC向け、利便性重視）
D) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 2
ユーザー登録時にメールアドレスの確認（メール認証）は行いますか？

A) 行わない（登録即利用可能 — PoC向け推奨）
B) 確認メール送信後にアカウント有効化
C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
アカウント削除時のデータ削除は物理削除と論理削除のどちらにしますか？

A) 物理削除（DBレコード・S3ファイルを即時完全削除 — PoC向け推奨）
B) 論理削除（deleted_atフラグで非表示化、一定期間後に物理削除）
C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4
個別セッション（generation_session）の削除時、関連する S3 上のメディアファイルも同時に削除しますか？

A) はい、セッション削除時にS3ファイルも即時削除
B) いいえ、S3ファイルは残し、DBレコードのみ削除
C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
パスワード要件の詳細はどのレベルにしますか？

A) 最低8文字、英字+数字必須（基本レベル）
B) 最低8文字、大文字+小文字+数字+記号各1文字必須（標準レベル）
C) 最低8文字のみ（PoC最小限）
D) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 6
`GenerationSession` のステータス管理はどの粒度で行いますか？

A) シンプル（created → media_uploaded → questions_answered → emotions_selected → generated → completed の6段階）
B) 最小限（created → in_progress → completed の3段階）
C) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 7
ユーザーごとに同時に保持できるアクティブなセッション数に制限を設けますか？

A) 制限なし（PoC向け推奨）
B) 同時アクティブ最大5セッション
C) 同時アクティブ最大1セッション（完了するまで新規不可）
D) Other (please describe after [Answer]: tag below)

[Answer]:C
