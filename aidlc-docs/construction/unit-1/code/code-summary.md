# Code Summary - Unit 1: Media Analysis

## 生成ファイル一覧

### ソースファイル（7ファイル）
| ファイル | 説明 |
|---|---|
| `backend/app/media/__init__.py` | モジュール初期化 |
| `backend/app/media/models.py` | SQLAlchemy モデル (MediaFile, ImageAnalysisResult, MusicAnalysisResult) + Pydantic スキーマ |
| `backend/app/media/validators.py` | ファイルバリデーション (MIME, サイズ, 拡張子整合性) |
| `backend/app/media/image_analyzer.py` | 画像解析 (Bedrock multimodal, 10解析項目) |
| `backend/app/media/music_analyzer.py` | 音楽解析 (Provider Pattern, メタデータ抽出 + Bedrock推定) |
| `backend/app/media/logic.py` | ビジネスロジック (upload_and_analyze, get_media_detail, get_presigned_url) |
| `backend/app/media/router.py` | APIルーター (3エンドポイント) |

### テストファイル（5ファイル）
| ファイル | テスト数 |
|---|---|
| `backend/tests/test_media_validators.py` | 19テスト — バリデーション全ルール |
| `backend/tests/test_image_analyzer.py` | 10テスト — JSONパース & フォールバック |
| `backend/tests/test_music_analyzer.py` | 10テスト — Provider Pattern & マージ動作 |
| `backend/tests/test_media_logic.py` | 8テスト — ロジック正常系/異常系/ロールバック |
| `backend/tests/test_media_router.py` | 8テスト — API正常/認証/権限/404 |

### マイグレーション（1ファイル）
| ファイル | 説明 |
|---|---|
| `backend/alembic/versions/002_media_tables.py` | media_files, image_analysis_results, music_analysis_results テーブル |

### 設定更新（2ファイル）
| ファイル | 変更内容 |
|---|---|
| `backend/requirements.txt` | `mutagen==1.47.0` 追加 |
| `backend/app/main.py` | media router 登録 |

## APIエンドポイント

| Method | Path | Status | 説明 |
|---|---|---|---|
| POST | `/api/media/upload` | 201 | メディアアップロード + AI解析（同期） |
| GET | `/api/media/{media_id}` | 200 | メディア詳細取得（解析結果 + presigned URL） |
| GET | `/api/media/{media_id}/presigned-url` | 200 | ダウンロード用プリサインドURL |

全エンドポイントで JWT 認証必須。

## ストーリー実装状況
| Story ID | 名称 | 実装状況 |
|---|---|---|
| US-2.1 | 画像アップロード | ✅ 完了 |
| US-2.2 | 音楽アップロード | ✅ 完了 |
| US-3.1 | メディア解析の完了通知 | ✅ 完了（同期レスポンスで即時返却） |

## アーキテクチャ特記事項

### Provider Pattern（音楽解析）
`MusicAnalysisProvider` Protocol を採用。将来的に外部API（Spotify, Essentia等）からBPM・キー・コード進行を取得する場合、新しいProviderクラスを実装してリストに追加するだけで切り替え可能。

```python
# 将来の拡張例
providers = [
    BedrockMusicProvider(),     # AI推定（ベースライン）
    SpotifyAnalysisProvider(),  # bpm, key を上書き
]
result = await analyze_music(file_data, file_name, providers=providers)
```
