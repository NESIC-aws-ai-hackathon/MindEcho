# Business Rules - Unit 1: Media Analysis

---

## 1. ファイルバリデーションルール

### BR-MEDIA-01: 画像ファイル許可形式
| MIMEタイプ | 拡張子 | 最大サイズ |
|---|---|---|
| image/jpeg | .jpg, .jpeg | 10MB |
| image/png | .png | 10MB |
| image/webp | .webp | 10MB |
| image/gif | .gif | 10MB |

### BR-MEDIA-02: 音楽ファイル許可形式
| MIMEタイプ | 拡張子 | 最大サイズ |
|---|---|---|
| audio/mpeg | .mp3 | 50MB |
| audio/wav, audio/x-wav | .wav | 50MB |
| audio/flac | .flac | 50MB |
| audio/aac, audio/mp4 | .aac, .m4a | 50MB |

### BR-MEDIA-03: MIMEタイプと拡張子の整合性チェック
- アップロード時、Content-Typeヘッダーのmedia typeとファイル名の拡張子を両方検証
- 両方が許可リストに含まれ、かつ整合すること（imageのMIMEなのに.mp3拡張子は拒否）
- 不整合時: 400 Bad Request「ファイル形式が一致しません」

### BR-MEDIA-04: ファイルサイズ制限
- 画像: 最大10MB（10,485,760 bytes）
- 音楽: 最大50MB（52,428,800 bytes）
- 超過時: 413 Payload Too Large

### BR-MEDIA-05: 空ファイル拒否
- ファイルサイズ 0 bytes のファイルは拒否
- エラー: 400 Bad Request「空のファイルはアップロードできません」

---

## 2. メディア種別判定ルール

### BR-MEDIA-06: 自動判定ロジック
- `media_type` パラメータ指定あり → そのまま使用（許可値: "image" | "music"）
- `media_type` パラメータ省略 → MIMEタイプのプレフィックスで判定:
  - `image/*` → "image"
  - `audio/*` → "music"
- 判定不能時: 400 Bad Request「メディア種別を判定できません」

### BR-MEDIA-07: media_typeパラメータバリデーション
- 許可値: "image", "music" のみ
- 不正値: 422 Validation Error

---

## 3. アップロードルール

### BR-MEDIA-08: セッション必須
- アップロードにはアクティブなセッション（status='created'）が必要
- session_id はリクエストボディまたは自動取得（ユーザーのアクティブセッション）

### BR-MEDIA-09: 1セッション1メディア制限
- 1つのGenerationSessionに対して MediaFile は1つのみ
- 既にMediaFileが存在するセッションへのアップロード: 409 Conflict
- メッセージ: 「このセッションには既にメディアがアップロードされています」

### BR-MEDIA-10: セッションステータス前提条件
- アップロード可能なステータス: `created` のみ
- その他のステータスでのアップロード試行: 400 Bad Request
- メッセージ: 「現在のセッション状態ではアップロードできません」

---

## 4. S3保存ルール

### BR-MEDIA-11: S3キー命名規則
- 形式: `{media_type}/{year}/{month}/{uuid}.{ext}`
- 例: `image/2026/05/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg`
- UUIDは新規生成（ファイル名の衝突回避）
- 年月はアップロード時点のUTC

### BR-MEDIA-12: Presigned URL生成
- 有効期限: 3600秒（1時間）
- プレビュー表示用に生成
- 期限切れ後は再取得が必要

---

## 5. AI解析ルール

### BR-MEDIA-13: 解析は同期実行
- アップロードAPIレスポンスに解析結果を含める
- クライアントはアップロード完了 = 解析完了として扱う

### BR-MEDIA-14: 解析リトライなし
- Bedrock呼び出し失敗時、自動リトライは行わない
- 失敗時は500 Internal Error を返す
- クライアント側で再アップロードによるリトライを想定

### BR-MEDIA-15: 解析レスポンスパースエラー耐性
- BedrockレスポンスがJSON形式でない場合:
  - raw_response に全文保存
  - 各フィールドにデフォルト値「分析できませんでした」を設定
  - エラーとはせず、正常レスポンスとして返す（PoC方針）

### BR-MEDIA-16: 画像解析の入力制約
- 画像はbase64エンコードしてBedrock Claude 3のマルチモーダル入力で送信
- 最大入力サイズ: Bedrock APIの制限に従う（通常20MB以下のbase64）

### BR-MEDIA-17: 音楽解析のメタデータ優先度
メタデータ抽出の優先度:
1. ID3v2タグ（MP3）
2. ID3v1タグ（MP3フォールバック）
3. Vorbis Comment（FLAC）
4. AAC/MP4メタデータ
5. ファイル名からの推定（最終手段）

---

## 6. エラーハンドリングルール

### BR-MEDIA-18: アップロードエラー一覧
| 状況 | HTTPステータス | コード | メッセージ |
|---|---|---|---|
| 非対応形式 | 400 | BAD_REQUEST | サポートされていないファイル形式です |
| MIME/拡張子不整合 | 400 | BAD_REQUEST | ファイル形式が一致しません |
| 空ファイル | 400 | BAD_REQUEST | 空のファイルはアップロードできません |
| セッション不正状態 | 400 | BAD_REQUEST | 現在のセッション状態ではアップロードできません |
| サイズ超過 | 413 | PAYLOAD_TOO_LARGE | ファイルサイズが上限を超えています |
| 二重アップロード | 409 | CONFLICT | このセッションには既にメディアがアップロードされています |
| S3アップロード失敗 | 500 | INTERNAL_ERROR | ファイルの保存に失敗しました |
| Bedrock解析失敗 | 500 | INTERNAL_ERROR | メディアの解析に失敗しました |

### BR-MEDIA-19: 部分失敗時のロールバック
- S3アップロード成功 → Bedrock解析失敗の場合:
  - MediaFileレコードは保存しない（トランザクションロールバック）
  - S3ファイルは削除を試みる（ベストエフォート）
  - 500エラーを返す
