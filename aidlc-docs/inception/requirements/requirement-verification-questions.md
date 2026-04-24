# Requirements Verification Questions

以下の質問に回答してください。各質問の `[Answer]:` タグの後に、選択肢の記号を記入してください。
どの選択肢にも当てはまらない場合は `X` を選び、その後に説明を追加してください。

---

## Question 1: アプリケーション形態
本サービスはどのプラットフォームで動作させますか？

A) Webアプリケーション（ブラウザベース）
B) モバイルアプリ（iOS / Android ネイティブ）
C) モバイルアプリ（React Native / Flutter 等のクロスプラットフォーム）
D) Webアプリケーション + PWA（モバイル対応含む）
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 2: バックエンド技術スタック
バックエンド（サーバーサイド）の技術に希望はありますか？

A) Python（FastAPI / Flask / Django）
B) TypeScript / JavaScript（Node.js / Express / NestJS）
C) Java / Kotlin（Spring Boot）
D) 特にこだわりなし（AI-DLCにおまかせ）
X) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 3: フロントエンド技術スタック
フロントエンド技術に希望はありますか？

A) React（Next.js）
B) Vue.js（Nuxt）
C) Svelte / SvelteKit
D) 特にこだわりなし（AI-DLCにおまかせ）
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 4: AI / LLM の活用方法
「おいしい誘惑」の提案に使用するAIはどのように実装しますか？

A) Amazon Bedrock（Claude等のFoundation Model）を利用
B) OpenAI API（GPT系）を利用
C) ローカルLLM（Ollama等）を利用
D) ルールベース＋食品データベースで実装（LLM不使用）
E) LLMとルールベースのハイブリッド（基本はルールベース、提案文の生成にLLM）
X) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 5: 食事記録の入力方法
ユーザーはどのように食事を記録しますか？

A) テキスト入力（自由記述 → AIが解析してカロリー推定）
B) 食品データベースから検索・選択
C) 写真撮影 → AI画像認識でメニュー判定
D) A + B の併用（テキスト入力 + データベース検索）
E) A + B + C すべて対応
X) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 6: 「目標ダメカロリー」の設定方法
ユーザーが1日に摂取すべき「ダメカロリー目標」はどう決定しますか？

A) ユーザーが手動で目標カロリーを設定する
B) 体重・身長・年齢等から自動計算し、「太るための推奨カロリー」を算出する
C) B + ユーザーが微調整できる
D) 固定値（例: 3000kcal）で全ユーザー共通
X) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 7: ユーザー認証・アカウント管理
ユーザー認証はどのレベルで必要ですか？

A) メールアドレス + パスワードによるアカウント登録
B) ソーシャルログイン（Google / Apple等）
C) A + B の両方対応
D) 認証不要（ローカルストレージのみで動作、ハッカソンMVP向け）
X) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 8: データ永続化
データの保存先はどうしますか？

A) クラウドデータベース（RDS / DynamoDB等）
B) サーバーレス（Firebase / Supabase等のBaaS）
C) ブラウザのローカルストレージ / IndexedDB（サーバーレス・ハッカソンMVP向け）
D) SQLite（軽量サーバーサイドDB）
X) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 9: 誘惑提案の具体性レベル
AIが提案する「おいしい誘惑」はどの程度具体的にしますか？

A) 食品名のみ（例: 「チーズバーガー」）
B) 食品名 + カロリー情報（例: 「チーズバーガー (約520kcal)」）
C) 食品名 + カロリー + 誘惑的な説明文（例: 「とろけるチーズとジューシーなパティの...」）
D) C + 近くのお店・コンビニの商品名まで含む
X) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 10: 「誘惑に負けた」記録の可視化
ユーザーが誘惑に負けた履歴はどのように表示しますか？

A) シンプルなリスト形式（日時 + 食べたもの + カロリー）
B) カレンダー形式（日ごとの「堕落度」を可視化）
C) グラフ・チャート形式（体重推移・カロリー推移を可視化）
D) B + C の両方
E) ゲーミフィケーション要素あり（「連続堕落記録」「誘惑マスター」等のバッジ）
X) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 11: デプロイ環境
本サービスはどこにデプロイしますか？

A) AWS（EC2 / ECS / Lambda等）
B) Vercel / Netlify（フロントエンド）+ AWS / その他（バックエンド）
C) ローカル実行のみ（ハッカソンデモ用）
D) コンテナ化してどこでも動作可能にする（Docker）
X) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 12: ハッカソンのスコープとタイムライン
本プロジェクトのスコープとタイムラインはどの程度ですか？

A) ハッカソン向けMVP（1〜2日で動くデモ）
B) プロトタイプ（1〜2週間で主要機能を実装）
C) 製品レベル（本格的な開発）
X) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 13: Security Extensions（セキュリティ拡張）
本プロジェクトでセキュリティ拡張ルールを適用しますか？

A) はい — すべてのセキュリティルールをブロッキング制約として適用する（本番レベルのアプリケーション推奨）
B) いいえ — セキュリティルールをスキップする（PoC・プロトタイプ・実験的プロジェクト向け）
X) Other (please describe after [Answer]: tag below)

[Answer]: 

---

## Question 14: Property-Based Testing Extension（プロパティベーステスト拡張）
本プロジェクトでプロパティベーステスト（PBT）ルールを適用しますか？

A) はい — すべてのPBTルールをブロッキング制約として適用する（ビジネスロジック・データ変換・シリアライゼーション・ステートフルコンポーネントを含むプロジェクト推奨）
B) 部分的 — 純粋関数とシリアライゼーションのラウンドトリップのみPBTルールを適用する
C) いいえ — PBTルールをスキップする（シンプルなCRUDアプリ・UIのみのプロジェクト向け）
X) Other (please describe after [Answer]: tag below)

[Answer]: A

---

すべての質問に回答が完了しましたら、チャットで「回答完了」とお知らせください。
