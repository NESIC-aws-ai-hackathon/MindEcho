# Functional Design Plan - Unit 1: Media Analysis

## 対象ストーリー（MVP）
| Story ID | 名称 | Priority |
|---|---|---|
| US-2.1 | 画像アップロード | Must Have (P1) |
| US-2.2 | 音楽アップロード | Must Have (P2) |
| US-3.1 | メディア解析の完了通知 | Must Have |

---

## 実行計画

### Part A: ドメインエンティティ設計
- [x] A1. `MediaFile` エンティティの属性・制約定義
- [x] A2. `ImageAnalysisResult` エンティティの属性定義
- [x] A3. `MusicAnalysisResult` エンティティの属性定義
- [x] A4. エンティティ間リレーション定義

### Part B: メディアアップロードビジネスロジック
- [x] B1. ファイルバリデーション（種別判定、サイズチェック、形式チェック）
- [x] B2. S3アップロードフロー（キー生成、保存、プレビューURL生成）
- [x] B3. セッションステータス遷移（created → media_uploaded）

### Part C: AI解析ビジネスロジック
- [x] C1. 画像解析フロー（Bedrockプロンプト設計、レスポンスパース）
- [x] C2. 音楽解析フロー（Bedrockプロンプト設計、レスポンスパース）
- [x] C3. 解析結果の正規化・保存ロジック

### Part D: ビジネスルール
- [x] D1. ファイルサイズ・形式制限ルール
- [x] D2. 解析エラーハンドリング（リトライ方針）
- [x] D3. セッション整合性ルール

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
画像解析でBedrockに抽出させる情報の粒度はどの程度にしますか？

A) 基本5項目（色彩、構図、雰囲気、被写体、ムード）— Application Design通り
B) 拡張8項目（上記 + テクスチャ、光の方向、感情的印象の記述）
C) 最小3項目（被写体、雰囲気、ムードのみ — PoC最小限）
D) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 2
音楽解析について、Bedrockに音楽ファイルを直接入力できない場合の代替手段はどうしますか？

A) メタデータ解析のみ（ファイル名、形式、サイズ、ID3タグ等から推定）— PoC向け
B) 音楽の波形特徴を簡易抽出（Python librosa等）した結果をBedrockにテキストとして渡す
C) ファイル名・ユーザーが入力する楽曲情報（タイトル、アーティスト）を元にBedrockに推定させる
D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
アップロードされたファイルのメディア種別判定ロジックはどうしますか？

A) MIMEタイプ + 拡張子の両方で判定（厳格）
B) MIMEタイプのみで判定（シンプル）
C) 拡張子のみで判定（最もシンプル — PoC向け）
D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 4
解析失敗時のリトライ方針はどうしますか？

A) リトライなし。失敗時はエラーレスポンスを返し、ユーザーに再アップロードを促す（PoC向け）
B) 自動リトライ1回（Bedrock呼び出しのみ）。2回目も失敗ならエラー
C) 自動リトライ3回（exponential backoff）。全て失敗ならエラー
D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 5
S3上のファイルキー（パス）の命名規則はどうしますか？

A) `{user_id}/{session_id}/{uuid}.{ext}`（ユーザー・セッション単位で整理）
B) `media/{uuid}.{ext}`（フラットに配置 — シンプル）
C) `{media_type}/{year}/{month}/{uuid}.{ext}`（種別・日付単位）
D) Other (please describe after [Answer]: tag below)

[Answer]: C

## Question 6
プレビューURL（画像表示・音楽再生用）はどの方式で提供しますか？

A) S3 Presigned URL（有効期限付き署名付きURL — 推奨）
B) CloudFront経由の公開URL
C) バックエンドプロキシ（GET /api/media/{id}/file でストリーミング）
D) Other (please describe after [Answer]: tag below)

[Answer]: A
