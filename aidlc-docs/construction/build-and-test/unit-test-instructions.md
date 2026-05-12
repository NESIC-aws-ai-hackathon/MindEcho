# Unit Test Execution — MindEcho

## テスト環境

- **テストフレームワーク**: pytest 8.3 + pytest-asyncio 0.24
- **テストDB**: SQLite in-memory（aiosqlite）
- **モック**: unittest.mock（AsyncMock）
- **HTTPテスト**: httpx AsyncClient（ASGI transport）

## テストファイル一覧

### Unit 0: Auth & Core Infrastructure
| ファイル | テスト内容 |
|---|---|
| `tests/test_auth_logic.py` | register, login, JWT, delete account |
| `tests/test_auth_router.py` | POST /register, POST /login, DELETE /account |
| `tests/test_data_logic.py` | session CRUD, delete |
| `tests/test_data_router.py` | GET/POST/DELETE /sessions |

### Unit 1: Media Analysis
| ファイル | テスト内容 |
|---|---|
| `tests/test_media_validators.py` | ファイル形式・サイズバリデーション |
| `tests/test_image_analyzer.py` | 画像解析プロンプト・パース |
| `tests/test_music_analyzer.py` | 音楽メタデータ抽出・Bedrock解析 |
| `tests/test_media_logic.py` | アップロード+解析統合ロジック |
| `tests/test_media_router.py` | POST /upload, GET /{id} |

### Unit 2: Cognitive Mapping
| ファイル | テスト内容 |
|---|---|
| `tests/test_question_generator.py` | 設問生成プロンプト・パース |
| `tests/test_emotion_generator.py` | 感情候補生成プロンプト・パース |
| `tests/test_cognitive_logic.py` | 回答送信、設問完了、感情選択 |
| `tests/test_cognitive_router.py` | 全6エンドポイント |

### Unit 3: Sentence Synthesis
| ファイル | テスト内容 |
|---|---|
| `tests/test_text_generator.py` | コンテクスト構築、プロンプト生成 |
| `tests/test_synthesis_logic.py` | 生成/再生成、上限、ステータス |
| `tests/test_synthesis_router.py` | 全3エンドポイント |

---

## テスト実行

### 1. 全ユニットテスト実行

```bash
cd backend
python -m pytest tests/ -v
```

### 2. ユニット別実行

```bash
# Unit 0
python -m pytest tests/test_auth_logic.py tests/test_auth_router.py tests/test_data_logic.py tests/test_data_router.py -v

# Unit 1
python -m pytest tests/test_media_validators.py tests/test_image_analyzer.py tests/test_music_analyzer.py tests/test_media_logic.py tests/test_media_router.py -v

# Unit 2
python -m pytest tests/test_question_generator.py tests/test_emotion_generator.py tests/test_cognitive_logic.py tests/test_cognitive_router.py -v

# Unit 3
python -m pytest tests/test_text_generator.py tests/test_synthesis_logic.py tests/test_synthesis_router.py -v
```

### 3. テスト結果確認

**期待される結果**:
- 全テスト PASSED
- 0 failures, 0 errors
- テスト実行時間: 数秒以内（in-memory SQLite使用）

### 4. テスト失敗時の対応

1. エラーメッセージを確認
2. 該当テストの fixture/mock 設定を確認
3. Bedrock/S3 関連は mock されていることを確認
4. DB スキーマ変更後は `conftest.py` の `Base.metadata.create_all` が全テーブルを含むことを確認
