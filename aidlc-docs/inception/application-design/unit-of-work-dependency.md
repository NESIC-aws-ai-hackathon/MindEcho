# Unit of Work Dependency - MindEcho

## 依存関係マトリクス

**行 → 列 = 「行が列に依存」**

| | Unit 0 | Unit 1 | Unit 2 | Unit 3 | Unit 4 | Unit F |
|---|---|---|---|---|---|---|
| **Unit 0** | — | — | — | — | — | — |
| **Unit 1** | ✓ | — | — | — | — | — |
| **Unit 2** | ✓ | ✓(R) | — | — | — | — |
| **Unit 3** | ✓ | ✓(R) | ✓(R) | — | ✓(stub) | — |
| **Unit 4** | ✓ | — | ✓(R) | ✓(R) | — | — |
| **Unit F** | ✓ | ✓ | ✓ | ✓ | — | — |

- ✓ = 直接依存（import / 関数呼び出し）
- ✓(R) = 読み取り専用依存（DBテーブルからのデータ参照）
- ✓(stub) = スタブ呼び出し（将来の拡張ポイント）

---

## 依存関係の詳細

### Unit 0 → (依存なし)
- 最下層の基盤ユニット。外部依存: AWS SDK (boto3), SQLAlchemy, PyJWT

### Unit 1 → Unit 0
- Core Module の S3クライアント、Bedrockクライアント、DB接続を利用
- 認証ミドルウェアによるリクエスト認証

### Unit 2 → Unit 0, Unit 1(R)
- Core Module の Bedrockクライアント、DB接続を利用
- Unit 1 の解析結果テーブル（`*_analysis_results`）からデータを読み取り

### Unit 3 → Unit 0, Unit 1(R), Unit 2(R), Unit 4(stub)
- Core Module の Bedrockクライアント、DB接続を利用
- Unit 1 の解析結果（AI解析リザルト表示用）を読み取り
- Unit 2 のコンテクスト回答・感情選択データを読み取り
- Unit 4 のスタブ関数を呼び出し（将来のパーソナライゼーション拡張ポイント）

### Unit 4 → Unit 0, Unit 2(R), Unit 3(R)
- Core Module の DB接続を利用
- Unit 2/3 の履歴データを学習用に読み取り（将来実装）

### Unit F → Unit 0, Unit 1, Unit 2, Unit 3
- 全バックエンドユニットのREST APIを呼び出し
- Unit 4 のAPIは呼び出さない（MVP対象外）

---

## 開発順序（ビルドオーダー）

```
Phase 1: Unit 0 (Auth & Core Infrastructure)
    │     └─ 全ユニットの前提基盤
    ▼
Phase 2: Unit 1 (Media Analysis)
    │     └─ Unit 0 に依存
    ▼
Phase 3: Unit 2 (Cognitive Mapping)
    │     └─ Unit 0, Unit 1 に依存
    ▼
Phase 4: Unit 3 (Sentence Synthesis)
    │     └─ Unit 0, Unit 1, Unit 2 に依存
    ▼
Phase 5: Unit 4 (Persona Tuning - Stub)
    │     └─ Unit 0 に依存（スタブのため最小限）
    ▼
Phase 6: Unit F (Frontend Integration)
          └─ 全バックエンドAPI完了後
```

### 開発順序の根拠
1. **Unit 0 が最初**: 全ユニットが依存する基盤（DB、認証、AWSクライアント）
2. **Unit 1 → 2 → 3 の順**: データフローの上流から下流へ（解析→認知→生成）
3. **Unit 4 はUnit 3の後**: スタブのみだが、Unit 3から呼ばれる拡張ポイントを定義するため
4. **Unit F が最後**: 全APIエンドポイントが利用可能な状態で統合実装

---

## 循環依存チェック

**結果: 循環依存なし** ✓

全依存は一方向（Unit 0 → Unit 1 → Unit 2 → Unit 3 → Unit 4 → Unit F）のレイヤー構造。
Unit 4 は Unit 2/3 を読み取り参照するが、Unit 2/3 は Unit 4 を直接参照しない（Unit 3 がスタブ呼び出しするのは将来の拡張ポイントのみ）。
