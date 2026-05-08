# Components - MindEcho

## アーキテクチャスタイル
**シンプルモジュール分割**: ユニットごとに `router` + `logic` + `models` の3ファイル構成。PoC規模に最適なシンプルさと、ユニット間の責務分離を両立。

---

## Backend Components (FastAPI)

### COMP-B01: Auth Module (`app/auth/`)
**責務**: ユーザー認証・アカウント管理  
**対応ユニット**: Unit 0  
**対応FR**: FR-7

| 責務項目 | 説明 |
|---|---|
| ユーザー登録 | メールアドレス + パスワードによる新規登録、bcryptハッシュ化 |
| ログイン | 認証情報検証、JWTアクセストークン発行 |
| パスワードリセット | リセットトークン生成・検証、新パスワード設定 |
| アカウント削除 | 関連データ一括削除（GDPR準拠） |

**インターフェース**: REST API (`/api/auth/*`)  
**依存**: Core Module（DB接続、設定）

---

### COMP-B02: Core Module (`app/core/`)
**責務**: 横断的関心事（設定管理、DB接続、ミドルウェア、外部サービスクライアント）  
**対応ユニット**: Unit 0  
**対応FR**: 全FR横断

| 責務項目 | 説明 |
|---|---|
| 設定管理 | 環境変数読み込み、アプリケーション設定 |
| DB接続 | SQLAlchemy セッション管理、マイグレーション設定 |
| 認証ミドルウェア | JWT検証、リクエストへのユーザー情報注入 |
| S3クライアント | boto3 S3操作の抽象化（アップロード/ダウンロード/削除） |
| Bedrockクライアント | boto3 Bedrock Runtime呼び出しの抽象化 |

**インターフェース**: Python モジュール（他コンポーネントからimport）  
**依存**: AWS SDK (boto3)、SQLAlchemy、環境変数

---

### COMP-B03: Media Module (`app/media/`)
**責務**: メディアアップロード・保存・解析  
**対応ユニット**: Unit 1 (Media Analysis Unit)  
**対応FR**: FR-1, FR-2

| 責務項目 | 説明 |
|---|---|
| メディアアップロード | ファイルバリデーション（形式・サイズ）、メディア種別判定 |
| S3保存 | アップロードファイルのS3保存、メタデータDB記録 |
| 画像解析 | AWS Bedrock による画像の情緒的メタデータ抽出 |
| 音楽解析 | AWS Bedrock による楽曲特徴量抽出 |
| 漫画解析 | AWS Bedrock による漫画ページの解析 |
| 小説解析 | AWS Bedrock による文章テキストの解析 |

**インターフェース**: REST API (`/api/media/*`)  
**依存**: Core Module（S3クライアント、Bedrockクライアント、DB）

**サブコンポーネント**:
- `analyzers/image_analyzer.py` — 画像解析ロジック
- `analyzers/music_analyzer.py` — 音楽解析ロジック
- `analyzers/manga_analyzer.py` — 漫画解析ロジック
- `analyzers/novel_analyzer.py` — 小説解析ロジック

---

### COMP-B04: Cognitive Module (`app/cognitive/`)
**責務**: コンテクスト設問生成・感情選択肢生成  
**対応ユニット**: Unit 2 (Cognitive Mapping Unit)  
**対応FR**: FR-3, FR-4

| 責務項目 | 説明 |
|---|---|
| コンテクスト設問生成 | 解析メタデータに基づきAIが動的に3〜5問の選択式設問を生成 |
| 設問回答受付 | ユーザーの選択式回答・自由記述の受付・保存 |
| 感情選択肢生成 | 解析結果+コンテクスト入力に基づき3〜5個の感情選択肢をAI生成 |
| 感情選択受付 | ユーザーの感情選択（複数可）の受付・保存 |

**インターフェース**: REST API (`/api/cognitive/*`)  
**依存**: Core Module（Bedrockクライアント、DB）、Media Module（解析結果参照）

---

### COMP-B05: Synthesis Module (`app/synthesis/`)
**責務**: 文章生成・出力管理  
**対応ユニット**: Unit 3 (Sentence Synthesis Unit)  
**対応FR**: FR-5

| 責務項目 | 説明 |
|---|---|
| 文章生成 | 感情+メタデータ+コンテクストを入力としたAI文章生成 |
| 出力形式制御 | SNS投稿/日記/レビューの3形式に応じた生成パラメータ調整 |
| 再生成 | 異なるバリエーションの文章再生成（セッションあたり10回制限） |
| 生成履歴管理 | 生成結果の保存・閲覧・削除 |

**インターフェース**: REST API (`/api/synthesis/*`)  
**依存**: Core Module（Bedrockクライアント、DB）、Cognitive Module（感情選択結果参照）

---

### COMP-B06: Data Module (`app/data/`)
**責務**: データ管理・エクスポート・プライバシー  
**対応ユニット**: Unit 0（横断）  
**対応FR**: FR-8

| 責務項目 | 説明 |
|---|---|
| 履歴一覧取得 | 生成履歴のページネーション付き一覧取得 |
| データ削除 | 個別/一括データ削除（S3ファイル含む） |
| データエクスポート | JSON形式での全ユーザーデータエクスポート |

**インターフェース**: REST API (`/api/data/*`)  
**依存**: Core Module（DB、S3クライアント）

---

## Frontend Components (Next.js)

### COMP-F01: LoginPage (`pages/login`)
**責務**: ログイン画面  
**対応US**: US-1.2  
- メールアドレス + パスワード入力フォーム
- バリデーション表示
- パスワードリセットリンク

### COMP-F02: RegisterPage (`pages/register`)
**責務**: ユーザー登録画面  
**対応US**: US-1.1  
- 登録フォーム（メール + パスワード + 確認パスワード）
- バリデーション表示

### COMP-F03: ResetPasswordPage (`pages/reset-password`)
**責務**: パスワードリセット画面  
**対応US**: US-1.3  
- メール入力 → リセットリンク送信
- トークン検証 → 新パスワード設定

### COMP-F04: UploadPage (`pages/upload`)
**責務**: メディアアップロード画面  
**対応US**: US-2.1〜US-2.4  
- メディア種別選択タブ（画像/音楽/漫画/小説）
- ファイルドロップゾーン / テキスト入力エリア
- プログレスバー、プレビュー表示

### COMP-F05: AnalyzingPage (`pages/analyzing`)
**責務**: 解析中の待機画面  
**対応US**: US-3.1  
- ローディングインジケーター
- 解析完了後の自動遷移

### COMP-F06: ContextPage (`pages/context`)
**責務**: コンテクスト設問回答画面  
**対応US**: US-4.1, US-4.2  
- 選択式設問カード（3〜5問）
- 自由記述テキストエリア
- スキップ/次へボタン

### COMP-F07: EmotionsPage (`pages/emotions`)
**責務**: 感情選択画面  
**対応US**: US-5.1  
- 感情選択肢カード（3〜5個、複数選択可）
- 選択状態のハイライト表示

### COMP-F08: GeneratePage (`pages/generate`)
**責務**: 出力形式選択 + 文章生成 + 結果表示  
**対応US**: US-6.1〜US-6.6  
- 出力形式ラジオボタン（SNS/日記/レビュー）
- 生成ボタン + ローディング
- 生成結果テキストエリア（編集可能）
- AI解析リザルト表示
- コピー/SNSシェア/再生成ボタン

### COMP-F09: HistoryPage (`pages/history`)
**責務**: 生成履歴一覧・詳細画面  
**対応US**: US-7.1, US-7.2, US-7.3  
- 生成履歴リスト（日時、メディア種別、出力形式）
- 詳細表示（生成文、感情、メディアプレビュー）
- 削除/エクスポートボタン

### COMP-F10: SettingsPage (`pages/settings`)
**責務**: アカウント設定・データ管理  
**対応US**: US-7.2, US-7.4（アカウント削除）  
- アカウント情報表示
- 全データ一括削除
- アカウント削除

---

## 共有フロントエンドコンポーネント

| コンポーネント | 責務 |
|---|---|
| `AuthGuard` | 認証状態チェック、未ログイン時のリダイレクト |
| `Layout` | 共通レイアウト（ヘッダー、ナビゲーション、フッター） |
| `Toast` | トースト通知表示（コピー成功等） |
| `ErrorBoundary` | エラーハンドリング・リトライUI |
