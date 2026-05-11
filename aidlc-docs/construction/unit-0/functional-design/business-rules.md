# Business Rules - Unit 0: Auth & Core Infrastructure

---

## 1. 認証ルール

### BR-AUTH-01: メールアドレスバリデーション
- RFC 5322準拠の形式チェック
- 保存時に lowercase 正規化
- 最大255文字
- UNIQUE制約（重複登録不可）

### BR-AUTH-02: パスワード要件
- 最低8文字（上限なし）
- 文字種制限なし（英字、数字、記号、日本語等すべて許可）
- 空白のみは不可

### BR-AUTH-03: パスワードハッシュ化
- アルゴリズム: bcrypt
- Cost factor: 12
- 平文パスワードはメモリ上でのみ保持（ログ出力禁止）

### BR-AUTH-04: JWT発行ルール
- アルゴリズム: HS256
- 有効期限: 24時間（発行時刻 + 86400秒）
- ペイロード: `sub`(user_id), `exp`(有効期限), `iat`(発行時刻)
- シークレットキー: 環境変数から取得（ハードコード禁止）

### BR-AUTH-05: 認証エラーメッセージの統一
- ユーザー未存在・パスワード不一致・アカウント削除済みいずれも同一メッセージ
- メッセージ: 「メールアドレスまたはパスワードが正しくありません」
- 目的: メールアドレスの存在有無を外部から推測不可能にする

### BR-AUTH-06: メール認証
- 実施しない（PoC）
- 登録完了と同時にアカウント有効化

---

## 2. セッション管理ルール

### BR-SESSION-01: 同時アクティブ制限
- ユーザーあたり同時にアクティブな（status ≠ 'completed'）セッションは **最大1つ**
- 制限超過時のレスポンス: 409 Conflict
- メッセージ: 「アクティブなセッションが存在します。完了してから新しいセッションを開始してください。」

### BR-SESSION-02: ステータス遷移ルール
- 順方向のみ許可: created → media_uploaded → questions_answered → emotions_selected → generated → completed
- スキップ不可（例: created → questions_answered は不可）
- 逆戻り不可（例: generated → emotions_selected は不可）
- 不正な遷移試行: 400 Bad Request

### BR-SESSION-03: ステータス遷移トリガー
| 現状態 | 次状態 | トリガーAPI |
|---|---|---|
| created | media_uploaded | POST /api/media/upload（Unit 1） |
| media_uploaded | questions_answered | POST /api/cognitive/answers（Unit 2） |
| questions_answered | emotions_selected | POST /api/cognitive/emotions/select（Unit 2） |
| emotions_selected | generated | POST /api/synthesis/generate（Unit 3） |
| generated | completed | POST /api/sessions/{id}/complete（Unit 0） |

### BR-SESSION-04: セッション完了
- generated 状態からのみ completed へ遷移可能
- completed 遷移後は再生成不可
- completed_at にタイムスタンプ記録

---

## 3. データ削除ルール

### BR-DELETE-01: 物理削除方針
- 全データ削除は物理削除（DBレコード完全消去 + S3ファイル削除）
- 論理削除（soft delete）は使用しない

### BR-DELETE-02: セッション削除のスコープ
セッション削除時に連鎖削除される関連データ:
1. `media_files` レコード
2. `image_analysis_results` または `music_analysis_results` レコード
3. `context_responses` レコード
4. `free_text_inputs` レコード
5. `emotion_selections` レコード
6. `generated_texts` レコード
7. S3上のメディアファイル

### BR-DELETE-03: アカウント削除のスコープ
アカウント削除時に連鎖削除されるデータ:
1. ユーザーの全GenerationSession（+ 上記BR-DELETE-02の範囲）
2. Userレコード本体

### BR-DELETE-04: 所有者チェック
- セッション削除はセッション所有者（user_id一致）のみ実行可能
- 不一致時: 403 Forbidden

### BR-DELETE-05: S3削除のエラー耐性
- S3削除が失敗してもDB削除は続行（PoC方針）
- 失敗はログに記録し、孤立ファイルとして許容
- 将来的にはバッチクリーンアップジョブで対応予定

---

## 4. バリデーションルール

### BR-VALID-01: リクエストボディバリデーション
| フィールド | ルール | エラーコード |
|---|---|---|
| email | RFC 5322形式、1〜255文字 | 422 INVALID_EMAIL |
| password | 8文字以上、空白のみ不可 | 422 INVALID_PASSWORD |
| session_id | UUID形式 | 422 INVALID_SESSION_ID |

### BR-VALID-02: バリデーションエラーレスポンス形式
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力内容に問題があります",
    "details": [
      {
        "field": "email",
        "code": "INVALID_EMAIL",
        "message": "有効なメールアドレス形式で入力してください"
      }
    ]
  }
}
```

---

## 5. エラーハンドリングルール

### BR-ERROR-01: エラーレスポンス統一形式
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "ユーザー向けメッセージ",
    "details": []
  }
}
```

### BR-ERROR-02: エラーコード体系
| HTTPステータス | コード | 用途 |
|---|---|---|
| 400 | BAD_REQUEST | リクエスト不正 |
| 401 | UNAUTHORIZED | 認証失敗 / トークン無効 |
| 403 | FORBIDDEN | 権限不足（他ユーザーリソース） |
| 404 | NOT_FOUND | リソース不存在 |
| 409 | CONFLICT | 重複（メール重複、セッション制限） |
| 413 | PAYLOAD_TOO_LARGE | ファイルサイズ超過 |
| 422 | VALIDATION_ERROR | バリデーション失敗 |
| 429 | TOO_MANY_REQUESTS | レート制限超過 |
| 500 | INTERNAL_ERROR | サーバー内部エラー |

### BR-ERROR-03: セキュリティ考慮
- 500エラー時に内部スタックトレースをレスポンスに含めない
- 認証エラーで具体的な失敗理由を明かさない（BR-AUTH-05参照）
- レート制限: MVP段階では未実装（将来対応）

---

## 6. 認証ミドルウェアルール

### BR-MW-01: 認証除外パス
以下のパスは認証不要（パブリック）:
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/health`（ヘルスチェック）

### BR-MW-02: 認証必須パス
上記以外の全APIエンドポイントは `Authorization: Bearer <token>` ヘッダー必須

### BR-MW-03: リクエストコンテキスト
認証成功時、以下の情報をリクエストスコープに格納:
- `current_user_id`: 認証ユーザーのUUID
- 各エンドポイントのロジックはこの値を使用してデータアクセスを制限
