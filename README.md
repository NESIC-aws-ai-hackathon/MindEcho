# MindEcho (マインドエコー) — 思考の外部委託プロトコル

> **「考えるのは、AIの仕事。あなたは、感じるだけでいい。」**

## 1. コンセプト
**MindEcho**は、人間が本来行うべき「内省」と「言語化」という知的な試行錯誤を、AIに完全にアウトソーシング（外部委託）させるための感情言語化支援サービスです。

優れた画像、音楽、映像などのメディアに触れた際、私たちは「名付けようのない感動」を覚えます。しかし、その正体を突き止め、解像度の高い言葉へと昇華させるプロセスは、極めて高い精神的コストと論理的思考を必要とします。

MindEchoは、ユーザーが抱える「言語化の壁」を取り払うのではなく、**「言語化という苦痛そのもの」を中抜き**します。メディアを読み込ませ、AIが提示する選択肢を数回タップするだけで、あたかも数時間かけて自己と向き合ったかのような、深く、論理的で、情緒あふれる「自分の感想（風の文章）」を生成します。

---

## 2. ハッカソンテーマとの適合性：何が人をダメにするのか
本サービスは、プログラマーの三大美徳である「怠慢」を、人間の「精神活動」という最後の聖域に適用しました。以下の3点において、極限まで「人をダメにする」ことを目指します。

### ① 内省（インサイト）の去勢
自分の感情の正体を探る「内省」は、自分自身を成長させる重要な機会です。MindEchoは、AIがメディアから「あなたが感じているはずの正解」を先回りして提示することで、ユーザーから自問自答する機会を奪います。ユーザーはAIのレールに乗るだけで、自分の内面を理解した気になれる「認知的安楽」に浸ることができます。

### ② 論理構築能力の退化
「Aという体験からBという感情が芽生え、ゆえにCと感じた」という論理の組み立ては、知的な筋力を必要とします。MindEchoは、断片的な単語から高度なレトリックを用いた文章を自動増幅するため、ユーザーが構成力を発揮する場面をゼロにします。使い続けるほどに、ユーザーは自力で140文字以上の文章を構成する能力を喪失していきます。

### ③ 自我の希薄化と依存
出力された「借り物の言葉」が、自分の拙い言葉よりも「自分らしい」と感じてしまう逆転現象を引き起こします。自分の思考をAI上の演算資源に依存させることで、このサービスなしでは「自分が何を考えているかさえ説明できない」という、精神的な自立を放棄した状態へとユーザーを導きます。

---

## 3. 主な機能 (Core Units)
- **Media Context Extraction**: 画像・音楽から「エモさの成分」を自動抽出。
- **Context Questionnaire**: メディアに応じたAI動的生成の選択式設問で、ユーザーの文脈を補完。
- **Emotional Annotation Wizard**: 「整理の手間」を排除する、タップ式の感情選択インターフェース。
- **Semantic Amplifier**: わずかな入力から、SNS投稿・日記・レビュー記事として「センスが良い」と評価されるレベルの文章へ超解像変換。
- **SNS Direct Share**: 生成文章をWeb Intent / Web Share APIでワンタップSNS投稿。

---

## 4. ビジネス意図 (Business Intent)
「自己表現の民主化」という甘美な言葉の裏で、人間から「言葉を紡ぐ苦労」を奪い去ること。
現代社会における「言語化コストの爆発」という課題に対し、解決ではなく **「思考の全自動化」** という極端なアプローチを提示することで、AI時代の新たな人間のあり方（＝思考を外注する存在）を定義します。

---

## 5. 技術スタック

| 領域 | 技術 |
|---|---|
| **Frontend** | React (Next.js) |
| **Backend** | Python (FastAPI) |
| **AI/ML** | AWS Bedrock (Claude/Titan) |
| **Database** | Amazon RDS (PostgreSQL) |
| **Storage** | Amazon S3 |
| **Authentication** | JWT + bcrypt |
| **Deploy** | AWS (ECS or Lambda + API Gateway) |

---

## 6. プロジェクト構成（モノレポ）

```
mindecho/
├── backend/                    # FastAPI バックエンド
│   ├── app/
│   │   ├── main.py
│   │   ├── core/              # 設定・DB・ミドルウェア・AWSクライアント
│   │   ├── auth/              # Unit 0: 認証
│   │   ├── media/             # Unit 1: メディア解析
│   │   │   └── analyzers/     # 画像/音楽 解析器
│   │   ├── cognitive/         # Unit 2: 認知マッピング
│   │   ├── synthesis/         # Unit 3: 文章合成
│   │   └── data/              # データ管理
│   ├── alembic/               # DBマイグレーション
│   └── tests/
├── frontend/                   # Next.js フロントエンド
│   ├── pages/                 # 10ページ構成
│   ├── components/            # 共有コンポーネント
│   ├── lib/                   # APIクライアント
│   └── types/                 # 型定義
├── aidlc-docs/                # AI-DLC設計ドキュメント
└── docker-compose.yml
```

---

## 7. ユニット構成

| Unit | 名称 | 責務 | MVP |
|---|---|---|---|
| Unit 0 | Auth & Core Infrastructure | 認証、DB基盤、AWSクライアント、データ管理 | ✓ |
| Unit 1 | Media Analysis | メディアアップロード、S3保存、AI解析（画像・音楽） | ✓ |
| Unit 2 | Cognitive Mapping | コンテクスト設問生成、感情選択肢生成 | ✓ |
| Unit 3 | Sentence Synthesis | 文章生成（3形式）、再生成、編集 | ✓ |
| Unit F | Frontend Integration | Next.js 全ページ実装 | ✓ |

**開発順**: Unit 0 → Unit 1 → Unit 2 → Unit 3 → Unit F

---

## 8. AI-DLCの実践

本プロジェクトは、AI-Driven Development Lifecycle（AI-DLC）に基づき、インセプションフェーズからAIを活用した意思決定を行っています。

### 完了済みフェーズ
- **Workspace Detection**: Greenfield プロジェクト検出
- **Requirements Analysis**: 8機能要件 + 6非機能要件の定義、技術スタック選定
- **User Stories**: 4ペルソナ、7ジャーニー、15 Must Haveストーリー（メディア対象: 画像+音楽）
- **Workflow Planning**: 実行計画策定（6ステージ実行、3ステージスキップ）
- **Application Design**: コンポーネント設計、APIエンドポイント設計（19本）、DBスキーマ設計（9テーブル）
- **Units Generation**: 5ユニット分解、依存関係定義、ストーリーマッピング

### 次フェーズ
- **CONSTRUCTION**: Per-Unit Functional Design → Code Generation → Build and Test

### 設計ドキュメント
設計成果物は `aidlc-docs/` 配下に格納:
- `aidlc-docs/inception/requirements/` — 要件定義
- `aidlc-docs/inception/user-stories/` — ペルソナ・ストーリー
- `aidlc-docs/inception/application-design/` — アプリケーション設計・ユニット定義