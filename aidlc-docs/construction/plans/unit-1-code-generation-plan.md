# Code Generation Plan - Unit 1: Media Analysis

## ユニットコンテキスト

### 対象ストーリー
| Story ID | 名称 | 実装内容 |
|---|---|---|
| US-2.1 | 画像アップロード | POST /api/media/upload (image) + 画像解析 |
| US-2.2 | 音楽アップロード | POST /api/media/upload (music) + 音楽解析 |
| US-3.1 | メディア解析の完了通知 | 解析結果をレスポンスで即時返却（同期処理） |

### 依存関係
- **Unit 0 への依存**: Core モジュール（database.py, s3_client.py, bedrock_client.py, middleware.py, exceptions.py）、GenerationSession モデル
- **他ユニットからの依存**: Unit 2 が MediaFile + AnalysisResult を参照（コンテクスト設問生成に使用）

### インターフェース
- `POST /api/media/upload` — メディアアップロード + AI解析（同期、multipart/form-data）
- `GET /api/media/{media_id}` — メディア詳細取得（解析結果込み）
- `GET /api/media/{media_id}/presigned-url` — ダウンロード用プリサインドURL

### データベースエンティティ
- **MediaFile** — メディアファイルメタデータ
- **ImageAnalysisResult** — 画像解析結果（10解析項目）
- **MusicAnalysisResult** — 音楽解析結果（8解析項目）

### 生成先パス
- **アプリケーションコード**: `backend/app/media/`
- **テスト**: `backend/tests/`
- **マイグレーション**: `backend/alembic/versions/`
- **ドキュメント**: `aidlc-docs/construction/unit-1/code/`

---

## 実行ステップ

### Step 1: Media モジュール — モデル定義
- [x] `backend/app/media/__init__.py`
- [x] `backend/app/media/models.py`
  - MediaFile SQLAlchemy モデル（9属性）
  - ImageAnalysisResult SQLAlchemy モデル（14属性）
  - MusicAnalysisResult SQLAlchemy モデル（18属性）
  - Pydantic スキーマ:
    - MediaUploadRequest (session_id, media_type)
    - MediaUploadResponse (media_file + analysis_result)
    - MediaDetailResponse (media_file + analysis + presigned_url)
    - ImageAnalysisResponse / MusicAnalysisResponse

### Step 2: Media モジュール — ファイルバリデーション
- [x] `backend/app/media/validators.py`
  - validate_file_size() — BR-MEDIA-04, BR-MEDIA-05
  - validate_mime_type() — BR-MEDIA-01, BR-MEDIA-02, BR-MEDIA-03
  - detect_media_type() — BR-MEDIA-06, BR-MEDIA-07
  - ALLOWED_IMAGE_TYPES / ALLOWED_MUSIC_TYPES 定義

### Step 3: Media モジュール — 画像解析ロジック
- [x] `backend/app/media/image_analyzer.py`
  - analyze_image(file_data: bytes) → ImageAnalysisResult データ
  - Bedrock プロンプト構築（10項目: colors〜style_characteristics）
  - base64 エンコード + マルチモーダル入力
  - レスポンスパース（JSON抽出 + フォールバック）

### Step 4: Media モジュール — 音楽解析ロジック
- [x] `backend/app/media/music_analyzer.py`
  - **プロバイダーパターン採用**: 属性ごとに解析ソースを切り替え可能な設計
  - MusicAnalysisProvider (Protocol) — 解析プロバイダーインターフェース
    - analyze(metadata: MusicMetadata) → dict  
  - BedrockMusicProvider — 現行デフォルト（全属性をBedrock推定）
    - Bedrock プロンプト構築（8項目: bpm〜emotional_impression）
    - レスポンスパース（JSON抽出 + フォールバック）
  - analyze_music(file_data, file_name, providers=None) → MusicAnalysisResult データ
    - メタデータ抽出（mutagen ライブラリ: ID3/Vorbis/AAC）
    - providers未指定時はBedrockMusicProviderをデフォルト使用
    - 各プロバイダーの結果をマージ（後勝ち: 外部API結果でAI結果を上書き）
  - **将来拡張ポイント**: 外部APIプロバイダー追加時はMusicAnalysisProviderを実装し、
    対象属性（bpm, key, chord_progression等）のみ返却すればAI結果を部分上書き可能

### Step 5: Media モジュール — ビジネスロジック
- [x] `backend/app/media/logic.py`
  - upload_and_analyze(session_id, user_id, file, media_type) → MediaUploadResponse
    - ファイルバリデーション
    - セッション検証（status == 'created', owner check）
    - S3アップロード（キー: {media_type}/{year}/{month}/{uuid}.{ext}）
    - MediaFile レコード保存
    - AI解析実行（画像/音楽分岐）
    - 解析結果保存
    - セッションステータス更新 → 'media_uploaded'
    - エラー時ロールバック（S3削除）
  - get_media_detail(media_id, user_id) → MediaDetailResponse
  - get_presigned_url(media_id, user_id) → str

### Step 6: Media モジュール — APIルーター
- [x] `backend/app/media/router.py`
  - POST /api/media/upload (multipart/form-data) → 201
    - UploadFile + Form fields (session_id, media_type?)
    - US-2.1, US-2.2, US-3.1 実装
  - GET /api/media/{media_id} → 200
  - GET /api/media/{media_id}/presigned-url → 200
  - 全エンドポイントに JWT 認証必須

### Step 7: ユニットテスト — バリデーション & 解析
- [x] `backend/tests/test_media_validators.py`
  - ファイルサイズバリデーションテスト
  - MIMEタイプ + 拡張子整合性テスト
  - メディア種別判定テスト
- [x] `backend/tests/test_image_analyzer.py`
  - Bedrockレスポンスのパーステスト（正常JSON）
  - パース失敗時フォールバックテスト
  - プロンプト構築テスト
- [x] `backend/tests/test_music_analyzer.py`
  - メタデータ抽出テスト（モック）
  - Bedrockレスポンスのパーステスト
  - メタデータ空時のフォールバックテスト

### Step 8: ユニットテスト — ロジック & API
- [x] `backend/tests/test_media_logic.py`
  - アップロード正常系テスト（画像/音楽）
  - セッション検証失敗テスト
  - S3アップロード後のBedrock失敗 → ロールバックテスト
  - メディア詳細取得テスト
  - 所有者チェックテスト
- [x] `backend/tests/test_media_router.py`
  - POST /api/media/upload 正常系（201）
  - ファイルサイズ超過（413）
  - 不正MIMEタイプ（400）
  - 認証なし（401）
  - 他ユーザーのセッション（403）
  - GET /api/media/{id} 正常系
  - GET /api/media/{id}/presigned-url 正常系

### Step 9: データベースマイグレーション
- [x] `backend/alembic/versions/002_media_tables.py`
  - media_files テーブル
  - image_analysis_results テーブル
  - music_analysis_results テーブル
  - FK制約 + インデックス

### Step 10: 依存関係更新 & main.py 統合
- [x] `backend/requirements.txt` に追加: `mutagen`
- [x] `backend/app/main.py` に media router を登録

### Step 11: ドキュメント生成
- [x] `aidlc-docs/construction/unit-1/code/code-summary.md`
  - 生成ファイル一覧
  - APIエンドポイント仕様
  - テスト一覧

---

## ストーリートレーサビリティ

| Story ID | 実装ステップ | 完了条件 |
|---|---|---|
| US-2.1 | Step 1〜6, 9 | 画像アップロード + 解析結果保存が動作 |
| US-2.2 | Step 1〜6, 9 | 音楽アップロード + 解析結果保存が動作 |
| US-3.1 | Step 5, 6 | 解析結果がレスポンスに含まれる（同期返却） |

---

## 合計スコープ
- **ソースファイル**: 7ファイル（models, validators, image_analyzer, music_analyzer, logic, router, __init__）
- **テストファイル**: 5ファイル
- **マイグレーション**: 1ファイル
- **設定更新**: 2ファイル（requirements.txt, pyproject.toml）
- **統合更新**: 1ファイル（main.py）
- **ドキュメント**: 1ファイル
