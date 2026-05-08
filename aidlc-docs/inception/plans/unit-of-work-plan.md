# Unit of Work Plan - MindEcho

## Execution Checklist

### Phase 1: ユニット定義
- [x] 各ユニットの責務・スコープ・境界の確定
- [x] ユニットごとの技術的詳細（ディレクトリ構成、主要ファイル）

### Phase 2: 依存関係マトリクス
- [x] ユニット間依存関係の定義
- [x] 開発順序（依存方向に基づくビルド順）の確定

### Phase 3: ストーリーマッピング
- [x] 全ユーザーストーリーの各ユニットへの割り当て
- [x] 未割り当てストーリーがないことの検証

### Phase 4: コード構成戦略
- [x] Greenfield向けディレクトリ構成ドキュメント化
- [x] ユニット間共有コード・共通モジュールの整理

### Phase 5: 検証
- [x] ユニット境界の整合性チェック
- [x] 全ストーリーカバレッジ確認

---

## クラリフィケーション質問

以下の質問に回答してください。各質問の `[Answer]:` タグの後に選択肢の文字を記入してください。

---

## Question 1
ユニットの開発・実行の分離方針はどちらを採用しますか？

A) モノレポ構成 — バックエンド（FastAPI）とフロントエンド（Next.js）を1つのリポジトリ内に配置（`/backend`、`/frontend` のトップレベルディレクトリ分離）
B) マルチレポ構成 — バックエンドとフロントエンドを別リポジトリで管理
C) お任せ（PoC規模に最適な構成を選定）
X) Other (please describe after [Answer]: tag below)

[Answer]:A

---

## Question 2
Unit 4（User Persona Tuning）はMVP対象外ですが、ユニット定義には含めますか？

A) 含める — 将来実装を見据えてインターフェース定義とスタブだけ用意する
B) 含めない — MVP対象ユニット（Unit 0〜3 + Frontend）のみ定義し、Unit 4は完全に後回し
C) お任せ
X) Other (please describe after [Answer]: tag below)

[Answer]:A

---

## Question 3
フロントエンド（Next.js）は独立したユニットとして扱いますか、それとも全バックエンドユニットのフロント統合として扱いますか？

A) 独立ユニット — Unit F として他バックエンドユニットと同列に扱う（独自のFunctional Design + Code Generation）
B) 統合フェーズ — 全バックエンドユニット完了後に「フロントエンド統合ユニット」として最後に実装
C) お任せ
X) Other (please describe after [Answer]: tag below)

[Answer]:B

---

## 回答方法
各質問の `[Answer]:` の後に、選択した文字（A, B, C, X等）を記入してください。
Xを選んだ場合は、その後に自由記述で説明を追加してください。

全ての回答が完了したら、お知らせください。
