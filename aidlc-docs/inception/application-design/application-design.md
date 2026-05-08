# Application Design - MindEcho（統合ドキュメント）

## 1. 設計判断サマリー

| 設計項目 | 決定 | 根拠 |
|---|---|---|
| バックエンドアーキテクチャ | シンプルモジュール分割 | Q1=D（お任せ）→ PoC規模に最適なシンプル構成を選定 |
| メディア解析実行方式 | 同期処理 | Q2=A — APIリクエスト内で解析を待ち結果を返す |
| フロントエンド構成 | ページ単位コンポーネント | Q3=A — ユーザージャーニーの各ステップ = 1ページ |
| DB解析結果格納 | 正規化テーブル | Q4=A — メディア種別ごとに解析結果テーブルを分離 |

---

## 2. システム構成概要

### バックエンド構成 (`app/`)
```
app/
├── main.py                    # FastAPIアプリケーションエントリポイント
├── core/                      # 横断的関心事
│   ├── config.py              # 環境変数・設定管理
│   ├── database.py            # SQLAlchemy セッション管理
│   ├── middleware.py          # JWT認証ミドルウェア
│   ├── s3_client.py           # S3操作抽象化
│   ├── bedrock_client.py      # Bedrock Runtime抽象化
│   └── exceptions.py         # 統一エラー型
├── auth/                      # Unit 0: 認証
│   ├── router.py
│   ├── logic.py
│   └── models.py
├── media/                     # Unit 1: メディア解析
│   ├── router.py
│   ├── logic.py
│   ├── models.py
│   └── analyzers/
│       ├── base.py            # 解析器基底クラス
│       ├── image_analyzer.py
│       └── music_analyzer.py
├── cognitive/                 # Unit 2: 認知マッピング
│   ├── router.py
│   ├── logic.py
│   └── models.py
├── synthesis/                 # Unit 3: 文章合成
│   ├── router.py
│   ├── logic.py
│   └── models.py
└── data/                      # データ管理
    ├── router.py
    ├── logic.py
    └── models.py
```

### フロントエンド構成 (`frontend/`)
```
frontend/
├── pages/
│   ├── login.tsx              # ログイン
│   ├── register.tsx           # ユーザー登録
│   ├── reset-password.tsx     # パスワードリセット
│   ├── upload.tsx             # メディアアップロード
│   ├── analyzing.tsx          # 解析中待機
│   ├── context.tsx            # コンテクスト設問
│   ├── emotions.tsx           # 感情選択
│   ├── generate.tsx           # 生成 + 結果表示
│   ├── history.tsx            # 履歴一覧
│   └── settings.tsx           # アカウント設定
├── components/
│   ├── AuthGuard.tsx          # 認証ガード
│   ├── Layout.tsx             # 共通レイアウト
│   ├── Toast.tsx              # トースト通知
│   └── ErrorBoundary.tsx      # エラーハンドリング
├── lib/
│   └── api.ts                 # APIクライアント（fetch wrapper）
└── types/
    └── index.ts               # 共通型定義
```

---

## 3. コンポーネント一覧

### バックエンド（6コンポーネント）

| ID | コンポーネント | モジュール | ユニット | 主要FR |
|---|---|---|---|---|
| COMP-B01 | Auth Module | `app/auth/` | Unit 0 | FR-7 |
| COMP-B02 | Core Module | `app/core/` | Unit 0 | 横断 |
| COMP-B03 | Media Module | `app/media/` | Unit 1 | FR-1, FR-2 |
| COMP-B04 | Cognitive Module | `app/cognitive/` | Unit 2 | FR-3, FR-4 |
| COMP-B05 | Synthesis Module | `app/synthesis/` | Unit 3 | FR-5 |
| COMP-B06 | Data Module | `app/data/` | Unit 0 | FR-8 |

### フロントエンド（10ページ + 4共有コンポーネント）

| ID | ページ | パス | 主要US |
|---|---|---|---|
| COMP-F01 | LoginPage | `/login` | US-1.2 |
| COMP-F02 | RegisterPage | `/register` | US-1.1 |
| COMP-F03 | ResetPasswordPage | `/reset-password` | US-1.3 |
| COMP-F04 | UploadPage | `/upload` | US-2.1〜2.4 |
| COMP-F05 | AnalyzingPage | `/analyzing` | US-3.1 |
| COMP-F06 | ContextPage | `/context` | US-4.1, US-4.2 |
| COMP-F07 | EmotionsPage | `/emotions` | US-5.1 |
| COMP-F08 | GeneratePage | `/generate` | US-6.1〜6.6 |
| COMP-F09 | HistoryPage | `/history` | US-7.1〜7.3 |
| COMP-F10 | SettingsPage | `/settings` | US-7.2, US-7.4 |

---

## 4. API エンドポイント一覧

| Method | Endpoint | Module | 認証 | 説明 |
|---|---|---|---|---|
| POST | `/api/auth/register` | Auth | 不要 | ユーザー登録 |
| POST | `/api/auth/login` | Auth | 不要 | ログイン |
| POST | `/api/auth/reset-password/request` | Auth | 不要 | パスワードリセット要求 |
| POST | `/api/auth/reset-password/confirm` | Auth | 不要 | パスワードリセット確認 |
| DELETE | `/api/auth/account` | Auth | 必要 | アカウント削除 |
| POST | `/api/media/upload` | Media | 必要 | メディアアップロード+解析（同期） |
| GET | `/api/media/{media_id}` | Media | 必要 | メディア詳細取得 |
| POST | `/api/cognitive/questions` | Cognitive | 必要 | コンテクスト設問生成 |
| POST | `/api/cognitive/answers` | Cognitive | 必要 | 設問回答送信 |
| POST | `/api/cognitive/emotions` | Cognitive | 必要 | 感情選択肢生成 |
| POST | `/api/cognitive/emotions/select` | Cognitive | 必要 | 感情選択送信 |
| POST | `/api/synthesis/generate` | Synthesis | 必要 | 文章生成 |
| POST | `/api/synthesis/regenerate` | Synthesis | 必要 | 文章再生成 |
| PUT | `/api/synthesis/{generation_id}` | Synthesis | 必要 | 生成テキスト更新 |
| GET | `/api/data/history` | Data | 必要 | 履歴一覧 |
| GET | `/api/data/history/{generation_id}` | Data | 必要 | 履歴詳細 |
| DELETE | `/api/data/history/{generation_id}` | Data | 必要 | 個別履歴削除 |
| DELETE | `/api/data/history` | Data | 必要 | 全履歴削除 |
| GET | `/api/data/export` | Data | 必要 | データエクスポート |

---

## 5. 依存関係サマリー

```
Frontend (Next.js)
    │
    │ REST API (JSON over HTTPS)
    ▼
┌─────────────────────────────┐
│  Core Module (横断基盤)      │
│  ┌────┐ ┌────┐ ┌────────┐  │
│  │ DB │ │ S3 │ │Bedrock │  │
│  └──┬─┘ └──┬─┘ └────┬───┘  │
├─────┼──────┼────────┼───────┤
│     │      │        │       │
│  Auth ─────┤        │       │
│     │      │        │       │
│  Media ────┴────────┤       │
│     │               │       │
│  Cognitive ─────────┤       │
│     │ (reads Media) │       │
│  Synthesis ─────────┘       │
│     │ (reads Media,Cognitive)│
│  Data ──────────────        │
└─────────────────────────────┘
```

**依存方向**: Auth → Core, Data / Media → Core / Cognitive → Core, Media(R) / Synthesis → Core, Media(R), Cognitive(R) / Data → Core

**循環依存**: なし（全依存は一方向）

---

## 6. セッションライフサイクル

ユーザージャーニーの一連の操作を `generation_sessions` テーブルで一元管理:

```
CREATED → MEDIA_UPLOADED → ANALYZED → CONTEXT_ANSWERED 
  → EMOTIONS_SELECTED → TEXT_GENERATED → COMPLETED
```

セッションIDがフロントエンドのページ遷移とバックエンドのデータ連携を橋渡しする中心的な識別子となる。

---

## 7. 関連設計ドキュメント

| ドキュメント | パス | 内容 |
|---|---|---|
| コンポーネント定義 | `components.md` | 各コンポーネントの責務・インターフェース詳細 |
| メソッドシグネチャ | `component-methods.md` | APIエンドポイント・メソッドの入出力型定義 |
| サービス設計 | `services.md` | サービスロジック・オーケストレーションフロー |
| 依存関係・データフロー | `component-dependency.md` | 依存関係マトリクス・DBスキーマ・データフロー図 |
