# Code Generation Plan - Unit F: Frontend Integration

## ユニットコンテキスト

### 対象ストーリー（Must Have のみ）
| Story ID | 名称 | 対応ページ |
|---|---|---|
| US-1.1 | ユーザー登録 | RegisterPage |
| US-1.2 | ログイン | LoginPage |
| US-2.1 | 画像アップロード | UploadPage |
| US-2.2 | 音楽アップロード | UploadPage |
| US-3.1 | 解析完了通知 | UploadPage（同期処理のため同一画面） |
| US-4.1 | コンテクスト設問回答 | ContextPage |
| US-4.2 | 自由記述入力 | ContextPage |
| US-5.1 | 感情選択 | EmotionsPage |
| US-6.1 | 出力形式選択 | GeneratePage |
| US-6.2 | 文章生成・結果表示 | GeneratePage |
| US-6.4 | 再生成 | GeneratePage |
| US-6.5 | 文章コピー | GeneratePage |
| US-6.6 | SNSシェア | GeneratePage |
| US-7.2 | データ削除 | HistoryPage |
| US-7.4 | アカウント削除 | SettingsPage |

### DEFERRED ストーリー（実装しない）
- US-1.3: パスワードリセット
- US-6.3: 文章編集
- US-7.1: 生成履歴閲覧（簡易版のみ実装）
- US-7.3: データエクスポート

### 依存関係
- Backend API: Unit 0〜3 全て完了済み（全エンドポイント利用可能）
- 生成先パス: `frontend/`（ワークスペースルート直下）
- ドキュメント: `aidlc-docs/construction/unit-f/code/`

### 実際のバックエンド API エンドポイント一覧
| Method | Path | Auth | 用途 |
|---|---|---|---|
| POST | `/api/auth/register` | No | ユーザー登録 |
| POST | `/api/auth/login` | No | ログイン |
| DELETE | `/api/auth/account` | Yes | アカウント削除 |
| POST | `/api/data/sessions` | Yes | 新規セッション作成 |
| GET | `/api/data/sessions` | Yes | セッション一覧 |
| DELETE | `/api/data/sessions/{id}` | Yes | セッション削除 |
| POST | `/api/media/upload` | Yes | メディアアップロード+解析 |
| GET | `/api/media/{media_id}` | Yes | メディア詳細取得 |
| GET | `/api/media/{media_id}/presigned-url` | Yes | Presigned URL取得 |
| POST | `/api/cognitive/responses` | Yes | 設問回答送信 |
| POST | `/api/cognitive/free-text` | Yes | 自由記述送信 |
| POST | `/api/cognitive/complete-questions` | Yes | 設問完了→感情候補生成 |
| POST | `/api/cognitive/emotions` | Yes | 感情選択送信 |
| GET | `/api/cognitive/questions/{session_id}` | Yes | 設問取得 |
| GET | `/api/cognitive/emotions/{session_id}` | Yes | 感情候補取得 |
| GET | `/api/synthesis/formats` | No | 出力形式一覧 |
| POST | `/api/synthesis/generate` | Yes | テキスト生成/再生成 |
| GET | `/api/synthesis/{session_id}` | Yes | 生成テキスト取得 |

---

## 技術スタック

- **Framework**: Next.js 14 (Pages Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 3
- **HTTP Client**: fetch API (カスタムラッパー)
- **State**: React useState/useEffect（状態管理ライブラリ不要 — PoC規模）
- **Auth Storage**: localStorage (JWT token)

---

## 実行ステップ

### Step 1: プロジェクト初期化 + 設定ファイル
- [x] Next.js プロジェクト初期化 (package.json + next.config.js + globals.css)
- [x] `frontend/tsconfig.json`
- [x] `frontend/tailwind.config.ts`
- [x] `frontend/postcss.config.js`
- [x] `frontend/.env.local.example`（NEXT_PUBLIC_API_URL）

### Step 2: 型定義 + API クライアント
- [x] `frontend/types/index.ts` — バックエンドレスポンス型定義
- [x] `frontend/lib/api.ts` — fetch ラッパー（JWT自動付与、エラーハンドリング）
- [x] `frontend/lib/auth.ts` — トークン保存/取得/削除ヘルパー

### Step 3: 共有コンポーネント
- [x] `frontend/components/Layout.tsx` — ヘッダー + ナビゲーション + フッター
- [x] `frontend/components/AuthGuard.tsx` — 認証チェック + リダイレクト
- [x] `frontend/components/Toast.tsx` — トースト通知
- [x] `frontend/components/ErrorBoundary.tsx` — エラーハンドリング

### Step 4: 認証ページ（US-1.1, US-1.2）
- [x] `frontend/pages/register.tsx` — ユーザー登録
- [x] `frontend/pages/login.tsx` — ログイン
- [x] `frontend/pages/_app.tsx` — 共通レイアウト適用
- [x] `frontend/pages/index.tsx` — ホーム（リダイレクト）

### Step 5: メディアアップロード（US-2.1, US-2.2, US-3.1）
- [x] `frontend/pages/upload.tsx` — メディア選択 + アップロード + 解析待ち

### Step 6: コンテクスト設問・感情選択（US-4.1, US-4.2, US-5.1）
- [x] `frontend/pages/context.tsx` — 設問表示 + 回答 + 自由記述
- [x] `frontend/pages/emotions.tsx` — 感情選択肢表示 + 選択

### Step 7: テキスト生成（US-6.1〜6.6）
- [x] `frontend/pages/generate.tsx` — 形式選択 + 生成 + 結果表示 + コピー + シェア + 再生成

### Step 8: データ管理（US-7.2, US-7.4）
- [x] `frontend/pages/history.tsx` — セッション一覧 + 削除
- [x] `frontend/pages/settings.tsx` — アカウント削除

### Step 9: ドキュメント生成
- [x] `aidlc-docs/construction/unit-f/code/code-summary.md`

---

## ファイル一覧（予定）

| # | パス | 種別 |
|---|---|---|
| 1 | frontend/package.json | 設定 |
| 2 | frontend/tsconfig.json | 設定 |
| 3 | frontend/tailwind.config.ts | 設定 |
| 4 | frontend/postcss.config.js | 設定 |
| 5 | frontend/.env.local.example | 設定 |
| 6 | frontend/types/index.ts | 型定義 |
| 7 | frontend/lib/api.ts | ユーティリティ |
| 8 | frontend/lib/auth.ts | ユーティリティ |
| 9 | frontend/components/Layout.tsx | 共有UI |
| 10 | frontend/components/AuthGuard.tsx | 共有UI |
| 11 | frontend/components/Toast.tsx | 共有UI |
| 12 | frontend/components/ErrorBoundary.tsx | 共有UI |
| 13 | frontend/pages/_app.tsx | エントリ |
| 14 | frontend/pages/index.tsx | ページ |
| 15 | frontend/pages/register.tsx | ページ |
| 16 | frontend/pages/login.tsx | ページ |
| 17 | frontend/pages/upload.tsx | ページ |
| 18 | frontend/pages/context.tsx | ページ |
| 19 | frontend/pages/emotions.tsx | ページ |
| 20 | frontend/pages/generate.tsx | ページ |
| 21 | frontend/pages/history.tsx | ページ |
| 22 | frontend/pages/settings.tsx | ページ |
| 23 | frontend/styles/globals.css | スタイル |
| 24 | aidlc-docs/construction/unit-f/code/code-summary.md | ドキュメント |

---

## 注意事項
- DEFERRED ストーリーのページ（reset-password）は作成しない
- パスワードリセット、文章編集、データエクスポートは MVP 対象外
- 解析は同期処理のためAnalyzingPage は不要（upload.tsx 内で完結）
- 履歴は簡易版（セッション一覧 + 削除のみ、詳細表示は DEFERRED）
- フロントエンドのテストは Build and Test ステージで扱う
