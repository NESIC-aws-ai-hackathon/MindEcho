# Unit F: フロントエンド統合 — コード生成サマリー

## 生成ファイル一覧

### 設定ファイル
| ファイル | 説明 |
|---|---|
| `frontend/package.json` | 依存関係定義 |
| `frontend/tsconfig.json` | TypeScript設定 |
| `frontend/tailwind.config.ts` | Tailwind CSS設定 |
| `frontend/postcss.config.js` | PostCSS設定 |
| `frontend/next.config.js` | Next.js設定 |
| `frontend/.env.local.example` | 環境変数テンプレート |
| `frontend/styles/globals.css` | グローバルスタイル |

### 基盤ファイル
| ファイル | 説明 |
|---|---|
| `frontend/types/index.ts` | バックエンドAPI型定義（Auth, Session, Media, Cognitive, Synthesis） |
| `frontend/lib/api.ts` | APIクライアント（fetch wrapper, JWT自動付与, 18関数） |
| `frontend/lib/auth.ts` | トークン管理ヘルパー |

### 共有コンポーネント
| ファイル | 説明 |
|---|---|
| `frontend/components/Layout.tsx` | ヘッダー + ナビ + フッター |
| `frontend/components/AuthGuard.tsx` | 認証チェック + リダイレクト |
| `frontend/components/Toast.tsx` | トースト通知 |
| `frontend/components/ErrorBoundary.tsx` | エラーハンドリング |

### ページコンポーネント
| ファイル | 対応US | 説明 |
|---|---|---|
| `frontend/pages/_app.tsx` | — | アプリケーションエントリ |
| `frontend/pages/index.tsx` | — | ホーム（リダイレクト） |
| `frontend/pages/login.tsx` | US-1.2 | ログイン |
| `frontend/pages/register.tsx` | US-1.1 | ユーザー登録 |
| `frontend/pages/upload.tsx` | US-2.1, US-2.2, US-3.1 | メディアアップロード + 解析 |
| `frontend/pages/context.tsx` | US-4.1, US-4.2 | コンテクスト設問 + 自由記述 |
| `frontend/pages/emotions.tsx` | US-5.1 | 感情選択 |
| `frontend/pages/generate.tsx` | US-6.1〜6.6 | 生成 + 結果 + コピー + シェア |
| `frontend/pages/history.tsx` | US-7.2 | セッション一覧 + 削除 |
| `frontend/pages/settings.tsx` | US-7.4 | アカウント削除 |

## ユーザーフロー

```
login/register → upload → context → emotions → generate
                                                   ↕
                                              history / settings
```

## API クライアント関数一覧

| 関数 | Method | Path |
|---|---|---|
| `register()` | POST | /api/auth/register |
| `login()` | POST | /api/auth/login |
| `deleteAccount()` | DELETE | /api/auth/account |
| `createSession()` | POST | /api/data/sessions |
| `listSessions()` | GET | /api/data/sessions |
| `deleteSession()` | DELETE | /api/data/sessions/{id} |
| `uploadMedia()` | POST | /api/media/upload |
| `getMediaDetail()` | GET | /api/media/{id} |
| `getQuestions()` | GET | /api/cognitive/questions/{id} |
| `submitResponses()` | POST | /api/cognitive/responses |
| `submitFreeText()` | POST | /api/cognitive/free-text |
| `completeQuestions()` | POST | /api/cognitive/complete-questions |
| `getEmotions()` | GET | /api/cognitive/emotions/{id} |
| `selectEmotions()` | POST | /api/cognitive/emotions |
| `getFormats()` | GET | /api/synthesis/formats |
| `generateText()` | POST | /api/synthesis/generate |
| `getGeneratedText()` | GET | /api/synthesis/{id} |

## 技術スタック

- Next.js 14 (Pages Router) + TypeScript
- Tailwind CSS 3
- fetch API（カスタムラッパー）
- localStorage（JWT保存）
