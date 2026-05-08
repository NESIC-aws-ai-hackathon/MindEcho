# Unit of Work - MindEcho

## ユニット構成概要

| Unit ID | 名称 | スコープ | MVP対象 | 開発順 |
|---|---|---|---|---|
| Unit 0 | Auth & Core Infrastructure | 認証、DB基盤、AWS接続、共通ミドルウェア | Yes | 1st |
| Unit 1 | Media Analysis | メディアアップロード、S3保存、AI解析（4種別） | Yes | 2nd |
| Unit 2 | Cognitive Mapping | コンテクスト設問生成、感情選択肢生成 | Yes | 3rd |
| Unit 3 | Sentence Synthesis | 文章生成、再生成、履歴管理 | Yes | 4th |
| Unit F | Frontend Integration | Next.js 全ページ実装 | Yes | 5th (最後) |

---

## Unit 0: Auth & Core Infrastructure

### 責務
- ユーザー認証（登録、ログイン、パスワードリセット、アカウント削除）
- JWT トークン発行・検証ミドルウェア
- PostgreSQL DB接続・セッション管理（SQLAlchemy）
- AWS S3 クライアント抽象化
- AWS Bedrock クライアント抽象化
- データ管理（履歴一覧、削除、エクスポート）
- 共通エラーハンドリング
- 設定管理（環境変数）

### バックエンドモジュール
- `app/core/` — config, database, middleware, s3_client, bedrock_client, exceptions
- `app/auth/` — router, logic, models
- `app/data/` — router, logic, models

### 主要テーブル
- `users`
- `generation_sessions`（セッションライフサイクル管理）

### 成果物
- DB マイグレーション（全テーブルスキーマ）
- 認証 API（5エンドポイント）
- データ管理 API（5エンドポイント）
- 共通基盤モジュール

---

## Unit 1: Media Analysis

### 責務
- メディアファイルアップロード（バリデーション、種別判定）
- S3 保存
- AI 解析（同期処理）: 画像 / 音楽
- 解析結果の正規化テーブルへの保存

### バックエンドモジュール
- `app/media/` — router, logic, models
- `app/media/analyzers/` — base, image_analyzer, music_analyzer

### 主要テーブル
- `media_files`
- `image_analysis_results`
- `music_analysis_results`

### 成果物
- メディアアップロード+解析 API（2エンドポイント）
- 2種別の解析器実装（Bedrock プロンプト設計含む）

---

## Unit 2: Cognitive Mapping

### 責務
- メディア解析結果に基づくコンテクスト設問の AI 動的生成（3〜5問）
- 設問回答の受付・保存
- 自由記述入力の受付・保存
- 解析結果 + コンテクスト入力に基づく感情選択肢の AI 生成（3〜5個）
- 感情選択の受付・保存

### バックエンドモジュール
- `app/cognitive/` — router, logic, models

### 主要テーブル
- `context_responses`
- `free_text_inputs`
- `emotion_selections`

### 成果物
- コンテクスト設問 API（4エンドポイント）
- 設問生成・感情生成の Bedrock プロンプト設計

---

## Unit 3: Sentence Synthesis

### 責務
- 全コンテクスト（解析結果 + 回答 + 感情）を統合した文章生成
- 出力形式制御（SNS / 日記 / レビュー）
- 再生成（セッションあたり10回制限）
- 生成テキストの編集保存

### バックエンドモジュール
- `app/synthesis/` — router, logic, models

### 主要テーブル
- `generated_texts`

### 成果物
- 文章生成 API（3エンドポイント）
- 文章生成 Bedrock プロンプト設計（3形式対応）

---

## Unit F: Frontend Integration

### 責務
- Next.js アプリケーション全体の実装
- 全10ページ（ログイン〜設定）
- 共有コンポーネント（AuthGuard, Layout, Toast, ErrorBoundary）
- API クライアント
- 型定義

### フロントエンドディレクトリ
- `frontend/pages/` — 10ページコンポーネント
- `frontend/components/` — 共有コンポーネント
- `frontend/lib/` — APIクライアント
- `frontend/types/` — 型定義

### 実装タイミング
- **全バックエンドユニット（Unit 0〜3）完了後に実装**
- バックエンドAPIが全て動作可能な状態で統合テスト可能

### 成果物
- Next.js プロジェクト全体
- 全ページ + コンポーネント実装
- APIクライアントによるバックエンド接続

---

## コード構成戦略（モノレポ）

```
mindecho/                          # ワークスペースルート
├── backend/                       # FastAPI バックエンド
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── auth/
│   │   ├── media/
│   │   │   └── analyzers/
│   │   ├── cognitive/
│   │   ├── synthesis/
│   │   └── data/
│   ├── alembic/                   # DBマイグレーション
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/                      # Next.js フロントエンド
│   ├── pages/
│   ├── components/
│   ├── lib/
│   ├── types/
│   ├── public/
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml             # ローカル開発用
├── .env.example
└── README.md
```
