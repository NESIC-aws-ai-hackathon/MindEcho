# Unit 3: テキスト生成・再生成 — コード生成サマリー

## 生成ファイル一覧

### ソースコード
| ファイル | 説明 |
|---|---|
| `backend/app/synthesis/__init__.py` | モジュール初期化 |
| `backend/app/synthesis/models.py` | GeneratedText モデル + Pydantic スキーマ |
| `backend/app/synthesis/text_generator.py` | コンテクスト構築 + プロンプト生成 + Bedrock 呼び出し |
| `backend/app/synthesis/logic.py` | 生成/再生成ビジネスロジック |
| `backend/app/synthesis/router.py` | FastAPI ルーター（3エンドポイント） |

### テスト
| ファイル | テストケース数 |
|---|---|
| `backend/tests/test_text_generator.py` | 13 テスト（4クラス） |
| `backend/tests/test_synthesis_logic.py` | 6 テスト（2クラス） |
| `backend/tests/test_synthesis_router.py` | 7 テスト（3クラス） |

### インフラ
| ファイル | 説明 |
|---|---|
| `backend/alembic/versions/004_synthesis_tables.py` | generated_texts テーブル作成マイグレーション |
| `backend/app/main.py` | synthesis_router 登録追加 |

## API エンドポイント

| メソッド | パス | 認証 | ステータス | 説明 |
|---|---|---|---|---|
| GET | `/api/synthesis/formats` | 不要 | 200 | 出力形式一覧取得 |
| POST | `/api/synthesis/generate` | 必要 | 201 | テキスト生成/再生成 |
| GET | `/api/synthesis/{session_id}` | 必要 | 200 | 生成済みテキスト取得 |

## データモデル

### generated_texts テーブル
| カラム | 型 | 制約 |
|---|---|---|
| id | String(36) | PK |
| session_id | String(36) | FK(generation_sessions.id), UNIQUE |
| output_format | String(20) | NOT NULL |
| generated_content | Text | NOT NULL |
| generation_count | Integer | NOT NULL, default=1 |
| created_at | DateTime(tz) | NOT NULL |
| updated_at | DateTime(tz) | NOT NULL |

## 主要設計ポイント

1. **生成/再生成統合API**: 同一 POST エンドポイントで初回生成・再生成を処理
2. **1レコード上書きモデル**: セッションあたり1レコード、再生成時は上書き
3. **再生成上限**: generation_count ≤ 10（失敗はカウントしない）
4. **3形式対応**: SNS投稿（140字）、日記（800字）、レビュー（400字）
5. **文字数制御**: プロンプトのみ（バックエンド検証なし）
6. **ステータス遷移**: emotions_selected → generated（生成時のみ遷移）
