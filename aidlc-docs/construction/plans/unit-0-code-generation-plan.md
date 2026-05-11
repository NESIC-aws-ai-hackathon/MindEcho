# Code Generation Plan - Unit 0: Auth & Core Infrastructure

## ユニットコンテキスト

### 対象ストーリー
| Story ID | 名称 | 実装内容 |
|---|---|---|
| US-1.1 | ユーザー登録 | POST /api/auth/register |
| US-1.2 | ログイン | POST /api/auth/login |
| US-7.2 | データの削除 | DELETE /api/data/sessions/{id} |
| US-7.4 | アカウント削除 | DELETE /api/auth/account |

### 依存関係
- 他ユニットへの依存: なし（Unit 0 は基盤ユニット）
- 他ユニットからの依存: Unit 1〜3, F が Core モジュール（DB, S3, Bedrock, Middleware）を利用

### 生成先パス
- **アプリケーションコード**: `backend/`（ワークスペースルート直下）
- **ドキュメント**: `aidlc-docs/construction/unit-0/code/`

---

## 実行ステップ

### Step 1: プロジェクト構造セットアップ
- [x] `backend/` ディレクトリ構造の作成
- [x] `backend/pyproject.toml`（依存関係定義）
- [x] `backend/requirements.txt`
- [x] `backend/.env.example`（環境変数テンプレート）
- [x] `docker-compose.yml`（PostgreSQL + LocalStack）

### Step 2: Core モジュール — 設定・DB接続
- [x] `backend/app/__init__.py`
- [x] `backend/app/core/__init__.py`
- [x] `backend/app/core/config.py`（環境変数読み込み、Settings クラス）
- [x] `backend/app/core/database.py`（SQLAlchemy async engine, session）

### Step 3: Core モジュール — 共通基盤
- [x] `backend/app/core/exceptions.py`（カスタム例外クラス + エラーレスポンス形式）
- [x] `backend/app/core/middleware.py`（JWT認証ミドルウェア）
- [x] `backend/app/core/s3_client.py`（S3操作の抽象化）
- [x] `backend/app/core/bedrock_client.py`（Bedrock呼び出しの抽象化）

### Step 4: Auth モジュール — モデル定義
- [x] `backend/app/auth/__init__.py`
- [x] `backend/app/auth/models.py`（User SQLAlchemy モデル、Pydantic スキーマ）

### Step 5: Auth モジュール — ビジネスロジック
- [x] `backend/app/auth/logic.py`（register, login, delete_account, JWT生成/検証）
  - US-1.1: register_user()
  - US-1.2: authenticate_user()
  - US-7.4: delete_account()

### Step 6: Auth モジュール — APIルーター
- [x] `backend/app/auth/router.py`（POST /register, POST /login, DELETE /account）

### Step 7: Data モジュール — モデル・ロジック・ルーター
- [x] `backend/app/data/__init__.py`
- [x] `backend/app/data/models.py`（GenerationSession SQLAlchemy モデル）
- [x] `backend/app/data/logic.py`（delete_session, delete_all_user_data）
  - US-7.2: delete_session()
- [x] `backend/app/data/router.py`（DELETE /sessions/{id}、GET /sessions）

### Step 8: FastAPI アプリケーションエントリポイント
- [x] `backend/app/main.py`（FastAPI app, ルーター登録, ミドルウェア設定, ヘルスチェック）

### Step 9: DBマイグレーション
- [x] `backend/alembic.ini`
- [x] `backend/alembic/env.py`
- [x] `backend/alembic/versions/001_initial_schema.py`（users + generation_sessions テーブル）

### Step 10: ユニットテスト — Auth
- [x] `backend/tests/__init__.py`
- [x] `backend/tests/conftest.py`（テスト用DBセッション、テストクライアント）
- [x] `backend/tests/test_auth_logic.py`（register, login, JWT, delete のロジックテスト）
- [x] `backend/tests/test_auth_router.py`（APIエンドポイントの統合テスト）

### Step 11: ユニットテスト — Data
- [x] `backend/tests/test_data_logic.py`（session削除、一括削除のロジックテスト）
- [x] `backend/tests/test_data_router.py`（APIエンドポイントの統合テスト）

### Step 12: ドキュメント生成
- [x] `aidlc-docs/construction/unit-0/code/code-summary.md`（生成ファイル一覧・実装サマリー）

---

## ファイル一覧（予定）

| # | パス | 種別 |
|---|---|---|
| 1 | backend/pyproject.toml | 設定 |
| 2 | backend/requirements.txt | 設定 |
| 3 | backend/.env.example | 設定 |
| 4 | docker-compose.yml | インフラ |
| 5 | backend/app/__init__.py | ソース |
| 6 | backend/app/core/__init__.py | ソース |
| 7 | backend/app/core/config.py | ソース |
| 8 | backend/app/core/database.py | ソース |
| 9 | backend/app/core/exceptions.py | ソース |
| 10 | backend/app/core/middleware.py | ソース |
| 11 | backend/app/core/s3_client.py | ソース |
| 12 | backend/app/core/bedrock_client.py | ソース |
| 13 | backend/app/auth/__init__.py | ソース |
| 14 | backend/app/auth/models.py | ソース |
| 15 | backend/app/auth/logic.py | ソース |
| 16 | backend/app/auth/router.py | ソース |
| 17 | backend/app/data/__init__.py | ソース |
| 18 | backend/app/data/models.py | ソース |
| 19 | backend/app/data/logic.py | ソース |
| 20 | backend/app/data/router.py | ソース |
| 21 | backend/app/main.py | ソース |
| 22 | backend/alembic.ini | 設定 |
| 23 | backend/alembic/env.py | ソース |
| 24 | backend/alembic/versions/001_initial_schema.py | ソース |
| 25 | backend/tests/__init__.py | テスト |
| 26 | backend/tests/conftest.py | テスト |
| 27 | backend/tests/test_auth_logic.py | テスト |
| 28 | backend/tests/test_auth_router.py | テスト |
| 29 | backend/tests/test_data_logic.py | テスト |
| 30 | backend/tests/test_data_router.py | テスト |
| 31 | aidlc-docs/construction/unit-0/code/code-summary.md | ドキュメント |

**合計**: 31ファイル（ソース12 + 設定4 + インフラ1 + テスト6 + マイグレーション3 + ドキュメント1 + init 4）
