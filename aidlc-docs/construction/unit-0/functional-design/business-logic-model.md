# Business Logic Model - Unit 0: Auth & Core Infrastructure

---

## 1. ユーザー登録フロー

### 処理シーケンス

```
Client                   API                      Logic                    DB
  │                       │                        │                       │
  │ POST /auth/register   │                        │                       │
  │──────────────────────►│                        │                       │
  │                       │ validate(email, pw)    │                       │
  │                       │───────────────────────►│                       │
  │                       │                        │ check_email_exists()  │
  │                       │                        │──────────────────────►│
  │                       │                        │◄──────────────────────│
  │                       │                        │                       │
  │                       │                        │ [email exists → 409]  │
  │                       │                        │                       │
  │                       │                        │ hash_password(pw)     │
  │                       │                        │ create_user(email, h) │
  │                       │                        │──────────────────────►│
  │                       │                        │◄──────────────────────│
  │                       │                        │ generate_jwt(user_id) │
  │                       │◄───────────────────────│                       │
  │ 201 { user_id, token }│                        │                       │
  │◄──────────────────────│                        │                       │
```

### ビジネスルール
1. メールアドレスを lowercase に正規化
2. 既存メールアドレスの重複チェック → 409 Conflict
3. パスワードを bcrypt でハッシュ化（cost=12）
4. User レコード作成
5. JWT アクセストークン発行（有効期限24時間）
6. レスポンスとして user_id + access_token を返却

---

## 2. ログインフロー

### 処理シーケンス

```
Client                   API                      Logic                    DB
  │                       │                        │                       │
  │ POST /auth/login      │                        │                       │
  │──────────────────────►│                        │                       │
  │                       │ validate(email, pw)    │                       │
  │                       │───────────────────────►│                       │
  │                       │                        │ find_user_by_email()  │
  │                       │                        │──────────────────────►│
  │                       │                        │◄──────────────────────│
  │                       │                        │                       │
  │                       │                        │ [not found → 401]    │
  │                       │                        │                       │
  │                       │                        │ verify_password(pw,h) │
  │                       │                        │                       │
  │                       │                        │ [mismatch → 401]     │
  │                       │                        │                       │
  │                       │                        │ generate_jwt(user_id) │
  │                       │◄───────────────────────│                       │
  │ 200 { user_id, token }│                        │                       │
  │◄──────────────────────│                        │                       │
```

### ビジネスルール
1. メールアドレスを lowercase に正規化して検索
2. ユーザー未存在・パスワード不一致ともに **同一のエラーメッセージ** を返す（情報漏洩防止）
   - エラーメッセージ: 「メールアドレスまたはパスワードが正しくありません」
3. bcrypt.verify で平文パスワードとハッシュを比較
4. 認証成功時に JWT アクセストークンを発行（24時間有効）

---

## 3. JWT トークン管理

### トークン仕様

| 項目 | 値 |
|---|---|
| アルゴリズム | HS256 |
| 有効期限 | 24時間 |
| ペイロード | `{ sub: user_id, exp: expiry_timestamp, iat: issued_at }` |
| シークレット | 環境変数 `JWT_SECRET_KEY` から取得 |

### トークン検証フロー
1. `Authorization: Bearer <token>` ヘッダーから抽出
2. 署名検証（HS256 + JWT_SECRET_KEY）
3. 有効期限チェック（exp < now → 401）
4. `sub` からユーザーIDを取得し、リクエストコンテキストに格納
5. ユーザーが存在するかDB確認（削除済みユーザーのトークン無効化）

### エラーケース
| 状況 | HTTPステータス | メッセージ |
|---|---|---|
| ヘッダー欠落 | 401 | Authentication required |
| トークン形式不正 | 401 | Invalid token format |
| 署名検証失敗 | 401 | Invalid token |
| 有効期限切れ | 401 | Token expired |
| ユーザー存在しない | 401 | Invalid token |

---

## 4. アカウント削除フロー

### 処理シーケンス

```
Client                   API           Auth Logic      Data Logic         DB          S3
  │                       │                │              │                │           │
  │ DELETE /auth/account  │                │              │                │           │
  │──────────────────────►│                │              │                │           │
  │                       │ verify_jwt()   │              │                │           │
  │                       │───────────────►│              │                │           │
  │                       │◄───────────────│              │                │           │
  │                       │                │              │                │           │
  │                       │ delete_all_user_data(user_id) │                │           │
  │                       │───────────────────────────────►│               │           │
  │                       │                │              │ get_sessions() │           │
  │                       │                │              │───────────────►│           │
  │                       │                │              │◄───────────────│           │
  │                       │                │              │                │           │
  │                       │                │              │ [per session]  │           │
  │                       │                │              │ get_s3_keys()  │           │
  │                       │                │              │───────────────►│           │
  │                       │                │              │ delete_s3()    │           │
  │                       │                │              │───────────────────────────►│
  │                       │                │              │                │           │
  │                       │                │              │ DELETE sessions CASCADE    │
  │                       │                │              │───────────────►│           │
  │                       │                │              │ DELETE user    │           │
  │                       │                │              │───────────────►│           │
  │                       │◄───────────────────────────────│               │           │
  │ 200 { message }       │                │              │                │           │
  │◄──────────────────────│                │              │                │           │
```

### 削除順序（データ整合性確保）
1. ユーザーの全GenerationSessionを取得
2. 各セッションに紐づくS3ファイルキーを収集
3. S3ファイルを一括削除（batch delete）
4. DB上のGenerationSession + 子テーブルをCASCADE DELETE
5. Userレコードを物理削除
6. 全操作をトランザクション内で実行（S3削除は先行、DB削除は後続）

### エラーハンドリング
- S3削除失敗: ログ記録のみ（DB削除は続行）— 孤立ファイルは許容（PoC）
- DB削除失敗: トランザクションロールバック → 500エラー

---

## 5. 個別セッション削除フロー

### 処理シーケンス
1. JWT認証でユーザーID確認
2. セッションIDの所有者チェック（user_id一致確認）
3. セッションに紐づくS3ファイルキーを取得
4. S3ファイル削除
5. GenerationSession + 子テーブルをCASCADE DELETE

### ビジネスルール
- 他ユーザーのセッションは削除不可（403 Forbidden）
- 存在しないセッションIDは404 Not Found
- 削除対象セッションのステータスは問わない（created〜completedいずれも削除可能）

---

## 6. セッション作成ロジック

### 同時アクティブセッション制限

```python
# 疑似コード
def create_session(user_id):
    active_count = count_sessions(
        user_id=user_id,
        status != 'completed'
    )
    if active_count >= 1:
        raise ConflictError(
            "アクティブなセッションが存在します。"
            "完了してから新しいセッションを開始してください。"
        )
    return create_new_session(user_id, status='created')
```

### ビジネスルール
- 同時にアクティブ（status ≠ 'completed'）なセッションは最大1つ
- 制限超過時は 409 Conflict で拒否
- completed 状態のセッションはカウント対象外
