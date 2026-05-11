# Code Summary - Unit 0: Auth & Core Infrastructure

## 生成ファイル一覧

### 設定・インフラ (5ファイル)
| パス | 説明 |
|---|---|
| `backend/pyproject.toml` | Pythonプロジェクト設定 |
| `backend/requirements.txt` | 依存パッケージ |
| `backend/.env.example` | 環境変数テンプレート |
| `docker-compose.yml` | PostgreSQL + LocalStack |
| `backend/alembic.ini` | Alembicマイグレーション設定 |

### Core モジュール (6ファイル)
| パス | 説明 |
|---|---|
| `backend/app/__init__.py` | パッケージ初期化 |
| `backend/app/core/__init__.py` | Coreパッケージ初期化 |
| `backend/app/core/config.py` | Settings (pydantic-settings) |
| `backend/app/core/database.py` | SQLAlchemy async engine + session |
| `backend/app/core/exceptions.py` | 統一エラーレスポンス体系 |
| `backend/app/core/middleware.py` | JWT認証依存関数 |
| `backend/app/core/s3_client.py` | S3操作ユーティリティ |
| `backend/app/core/bedrock_client.py` | Bedrock呼び出しユーティリティ |

### Auth モジュール (4ファイル)
| パス | 説明 |
|---|---|
| `backend/app/auth/__init__.py` | パッケージ初期化 |
| `backend/app/auth/models.py` | User SQLAlchemy model + Pydantic schemas |
| `backend/app/auth/logic.py` | register, login, delete_account, JWT |
| `backend/app/auth/router.py` | POST /register, POST /login, DELETE /account |

### Data モジュール (4ファイル)
| パス | 説明 |
|---|---|
| `backend/app/data/__init__.py` | パッケージ初期化 |
| `backend/app/data/models.py` | GenerationSession model + schemas |
| `backend/app/data/logic.py` | create, delete, list sessions |
| `backend/app/data/router.py` | GET/POST /sessions, DELETE /sessions/{id} |

### エントリポイント (1ファイル)
| パス | 説明 |
|---|---|
| `backend/app/main.py` | FastAPI app + CORS + error handlers + health |

### DBマイグレーション (2ファイル)
| パス | 説明 |
|---|---|
| `backend/alembic/env.py` | Alembic async環境設定 |
| `backend/alembic/versions/001_initial_schema.py` | users + generation_sessions テーブル |

### テスト (6ファイル)
| パス | 説明 |
|---|---|
| `backend/tests/__init__.py` | パッケージ初期化 |
| `backend/tests/conftest.py` | テストDB + HTTPクライアント fixtures |
| `backend/tests/test_auth_logic.py` | パスワードハッシュ + JWT テスト |
| `backend/tests/test_auth_router.py` | 登録・ログイン・削除 APIテスト |
| `backend/tests/test_data_logic.py` | セッションCRUD + 制限テスト |
| `backend/tests/test_data_router.py` | Data APIエンドポイントテスト |

---

## APIエンドポイント

| Method | Path | 認証 | ストーリー |
|---|---|---|---|
| POST | /api/auth/register | 不要 | US-1.1 |
| POST | /api/auth/login | 不要 | US-1.2 |
| DELETE | /api/auth/account | 必要 | US-7.4 |
| GET | /api/data/sessions | 必要 | — |
| POST | /api/data/sessions | 必要 | — |
| DELETE | /api/data/sessions/{id} | 必要 | US-7.2 |
| GET | /api/health | 不要 | — |

---

## 実装したビジネスルール

- BR-AUTH-01〜06: メール正規化、パスワード8文字最低、bcrypt cost=12、JWT 24h HS256、統一エラーメッセージ
- BR-SESSION-01: 同時アクティブセッション最大1
- BR-SESSION-02: 6段階ステータス遷移（順方向のみ）
- BR-DELETE-01〜05: 物理削除、CASCADE、S3連動削除
- BR-ERROR-01〜03: 統一エラー形式、スタックトレース非公開
- BR-MW-01〜03: パブリックパス除外、Bearer必須、コンテキスト注入

---

## 起動方法

```bash
# 依存サービス起動
docker compose up -d

# Python環境セットアップ
cd backend
pip install -r requirements.txt

# DBマイグレーション
alembic upgrade head

# サーバー起動
uvicorn app.main:app --reload --port 8000

# テスト実行
pip install aiosqlite  # テスト用追加依存
pytest
```
