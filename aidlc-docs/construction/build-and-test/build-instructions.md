# Build Instructions — MindEcho

## Prerequisites

| 項目 | 要件 |
|---|---|
| OS | Windows / macOS / Linux |
| Python | 3.11+ |
| Node.js | 18+ (LTS) |
| Docker | Docker Desktop（PostgreSQL + LocalStack 用） |
| Git | 2.x |

## 環境変数

バックエンド: `backend/.env`（`.env.example` をコピー）
フロントエンド: `frontend/.env.local`（`.env.local.example` をコピー）

---

## 1. インフラ起動（Docker）

```bash
# ワークスペースルートで実行
docker-compose up -d

# 起動確認
docker-compose ps
# db (postgres:16-alpine) — healthy
# localstack (localstack/localstack:3.0) — running
```

### LocalStack S3 バケット作成

```bash
aws --endpoint-url=http://localhost:4566 s3 mb s3://mindecho-media
```

---

## 2. バックエンドビルド

```bash
cd backend

# 仮想環境作成
python -m venv .venv

# 仮想環境有効化
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
pip install aiosqlite  # テスト用（SQLite async driver）

# 環境変数設定
cp .env.example .env
# .env を編集: JWT_SECRET_KEY を任意の値に設定
```

### DB マイグレーション

```bash
# マイグレーション実行
alembic upgrade head

# テーブル確認
# psql -U mindecho -h localhost -d mindecho -c "\dt"
# 期待: users, generation_sessions, media_files, image_analysis_results,
#       music_analysis_results, context_questions, context_responses,
#       free_text_inputs, emotion_candidates, emotion_selections,
#       generated_texts
```

### バックエンド起動確認

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ヘルスチェック
curl http://localhost:8000/docs
# → Swagger UI が表示されれば成功
```

---

## 3. フロントエンドビルド

```bash
cd frontend

# 依存関係インストール
npm install

# 環境変数設定
cp .env.local.example .env.local

# ビルド確認
npm run build

# 開発サーバー起動
npm run dev
# → http://localhost:3000 でアクセス可能
```

---

## 4. ビルド成果物

| コンポーネント | 成果物 | 場所 |
|---|---|---|
| Backend | Python パッケージ | `backend/app/` |
| Backend DB | マイグレーション済み DB | PostgreSQL |
| Frontend | Next.js ビルド | `frontend/.next/` |
| Infrastructure | Docker コンテナ | PostgreSQL + LocalStack |

---

## トラブルシューティング

### `asyncpg` 接続エラー
- **原因**: PostgreSQL が起動していない
- **解決**: `docker-compose up -d db` で起動確認

### `aiosqlite` が見つからない（テスト時）
- **原因**: テスト用依存が未インストール
- **解決**: `pip install aiosqlite`

### LocalStack 接続エラー
- **原因**: LocalStack コンテナが起動していない
- **解決**: `docker-compose up -d localstack`

### フロントエンド `npm run build` エラー
- **原因**: Node.js バージョン不足
- **解決**: Node.js 18+ をインストール
