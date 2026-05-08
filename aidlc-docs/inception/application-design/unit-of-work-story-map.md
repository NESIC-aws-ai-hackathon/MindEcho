# Unit of Work Story Map - MindEcho

## ストーリー割り当て一覧

| Story ID | ストーリー名 | Unit | Priority |
|---|---|---|---|
| US-1.1 | ユーザー登録 | Unit 0 | Must Have |
| US-1.2 | ログイン | Unit 0 | Must Have |
| US-1.3 | パスワードリセット | Unit 0 | Should Have |
| US-2.1 | 画像アップロード | Unit 1 | Must Have (P1) |
| US-2.2 | 音楽アップロード | Unit 1 | Must Have (P2) |
| US-2.3 | 漫画ページアップロード | Unit 1 | Should Have (P3) |
| US-2.4 | 小説・テキスト入力 | Unit 1 | Should Have (P4) |
| US-3.1 | メディア解析の完了通知 | Unit 1 | Must Have |
| US-4.1 | コンテクスト設問への回答 | Unit 2 | Must Have |
| US-4.2 | 自由記述による補足入力 | Unit 2 | Must Have |
| US-5.1 | 感情選択肢の選択 | Unit 2 | Must Have |
| US-6.1 | 出力形式の選択 | Unit 3 | Must Have |
| US-6.2 | 文章生成と結果表示 | Unit 3 | Must Have |
| US-6.3 | 文章の編集 | Unit 3 | Should Have |
| US-6.4 | 文章の再生成 | Unit 3 | Must Have |
| US-6.5 | 文章のコピー | Unit F | Must Have |
| US-6.6 | SNSへの直接投稿 | Unit F | Must Have |
| US-7.1 | 生成履歴の閲覧 | Unit 0 | Should Have |
| US-7.2 | データの削除 | Unit 0 | Must Have |
| US-7.3 | データエクスポート | Unit 0 | Should Have |
| US-7.4 | アカウント削除 | Unit 0 | Must Have |

---

## ユニット別ストーリー集約

### Unit 0: Auth & Core Infrastructure（7ストーリー）
| Story ID | 名称 | Priority |
|---|---|---|
| US-1.1 | ユーザー登録 | Must Have |
| US-1.2 | ログイン | Must Have |
| US-1.3 | パスワードリセット | Should Have |
| US-7.1 | 生成履歴の閲覧 | Should Have |
| US-7.2 | データの削除 | Must Have |
| US-7.3 | データエクスポート | Should Have |
| US-7.4 | アカウント削除 | Must Have |

### Unit 1: Media Analysis（5ストーリー）
| Story ID | 名称 | Priority |
|---|---|---|
| US-2.1 | 画像アップロード | Must Have (P1) |
| US-2.2 | 音楽アップロード | Must Have (P2) |
| US-2.3 | 漫画ページアップロード | Should Have (P3) |
| US-2.4 | 小説・テキスト入力 | Should Have (P4) |
| US-3.1 | メディア解析の完了通知 | Must Have |

### Unit 2: Cognitive Mapping（3ストーリー）
| Story ID | 名称 | Priority |
|---|---|---|
| US-4.1 | コンテクスト設問への回答 | Must Have |
| US-4.2 | 自由記述による補足入力 | Must Have |
| US-5.1 | 感情選択肢の選択 | Must Have |

### Unit 3: Sentence Synthesis（4ストーリー）
| Story ID | 名称 | Priority |
|---|---|---|
| US-6.1 | 出力形式の選択 | Must Have |
| US-6.2 | 文章生成と結果表示 | Must Have |
| US-6.3 | 文章の編集 | Should Have |
| US-6.4 | 文章の再生成 | Must Have |

### Unit 4: User Persona Tuning（0ストーリー）
- MVP対象外。スタブのみ実装。
- 将来対応: FR-6.1, FR-6.2, FR-6.3（ユーザーストーリー未作成）

### Unit F: Frontend Integration（2ストーリー + 全ページUI実装）
| Story ID | 名称 | Priority |
|---|---|---|
| US-6.5 | 文章のコピー | Must Have |
| US-6.6 | SNSへの直接投稿 | Must Have |

**Note**: Unit F は上記2ストーリーの固有ロジック（クリップボード操作、Web Share API）を担当するほか、全バックエンドユニットのUIを統合実装する。各ページのUI実装は対応するバックエンドストーリーのフロントエンド対応として扱う。

---

## カバレッジ検証

- **全ストーリー数**: 21
- **割り当て済み**: 21
- **未割り当て**: 0 ✓

全ユーザーストーリーがいずれかのユニットに割り当て済みであることを確認。
