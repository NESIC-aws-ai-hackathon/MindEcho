# Integration Test Instructions — MindEcho

## 目的

ユニット間の連携が正しく動作することを検証する。特にユーザージャーニー全体を通した一連のAPI呼び出しシーケンスをテストする。

---

## テスト環境セットアップ

### 1. インフラ起動

```bash
docker-compose up -d
```

### 2. バックエンド起動

```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. LocalStack S3 バケット作成

```bash
aws --endpoint-url=http://localhost:4566 s3 mb s3://mindecho-media
```

---

## 統合テストシナリオ

### シナリオ 1: 画像ジャーニー（E2E API フロー）

**テスト対象**: Unit 0 → Unit 1 → Unit 2 → Unit 3

```bash
BASE=http://localhost:8000

# 1. ユーザー登録
curl -s -X POST $BASE/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"integration@test.com","password":"testpass123"}' \
  | jq .
# → access_token を取得
TOKEN="<取得したtoken>"

# 2. セッション作成
curl -s -X POST $BASE/api/data/sessions \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
# → session.id を取得
SESSION_ID="<取得したsession_id>"

# 3. 画像アップロード + 解析
curl -s -X POST $BASE/api/media/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_image.jpg" \
  -F "session_id=$SESSION_ID" \
  -F "media_type=image" \
  | jq .
# → 期待: media_file + image_analysis が返る
# → media_file.id を取得

# 4. コンテクスト設問取得
curl -s -X GET $BASE/api/cognitive/questions/$SESSION_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
# → 期待: 3〜5問の選択式設問

# 5. 設問回答送信
curl -s -X POST $BASE/api/cognitive/responses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "responses": [
      {"question_id": "<Q1のID>", "selected_choice": "A"},
      {"question_id": "<Q2のID>", "selected_choice": "B"},
      {"question_id": "<Q3のID>", "selected_choice": "C"}
    ]
  }' | jq .

# 6. 設問完了 → 感情候補生成
curl -s -X POST $BASE/api/cognitive/complete-questions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "'$SESSION_ID'"}' \
  | jq .
# → 期待: 3〜5個の感情候補

# 7. 感情選択
curl -s -X POST $BASE/api/cognitive/emotions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "candidate_ids": ["<候補1のID>", "<候補2のID>"]
  }' | jq .

# 8. テキスト生成
curl -s -X POST $BASE/api/synthesis/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "output_format": "sns"
  }' | jq .
# → 期待: 201, generated_content が返る

# 9. 再生成（別形式）
curl -s -X POST $BASE/api/synthesis/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "'$SESSION_ID'",
    "output_format": "diary"
  }' | jq .
# → 期待: generation_count=2

# 10. 生成テキスト取得
curl -s -X GET $BASE/api/synthesis/$SESSION_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
# → 期待: 最新の生成テキスト

# 11. セッション一覧確認
curl -s -X GET "$BASE/api/data/sessions?page=1" \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
# → 期待: 1件のセッション（status=generated）

# 12. セッション削除
curl -s -X DELETE $BASE/api/data/sessions/$SESSION_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
```

**期待される結果**:
- 各ステップで正常レスポンス
- ステータス遷移: created → media_uploaded → questions_generated → questions_answered → emotions_selected → generated
- 生成テキストがメディア解析結果+コンテクスト+感情を反映

---

### シナリオ 2: 認証エラー検証

```bash
# 未認証でのアクセス（401）
curl -s -X POST $BASE/api/data/sessions | jq .
# → 期待: 401 Unauthorized

# 無効なトークン（401）
curl -s -X GET $BASE/api/data/sessions \
  -H "Authorization: Bearer invalid-token" | jq .
# → 期待: 401 Unauthorized

# 他ユーザーのセッションアクセス（403 or 404）
# → 期待: アクセス拒否
```

---

### シナリオ 3: 出力形式一覧（認証不要）

```bash
curl -s -X GET $BASE/api/synthesis/formats | jq .
# → 期待: 3形式（sns, diary, review）、認証なしでアクセス可能
```

---

## フロントエンド統合テスト（手動）

### 前提
- バックエンド起動済み（http://localhost:8000）
- フロントエンド起動済み（http://localhost:3000）

### テスト手順

1. **登録**: http://localhost:3000/register でアカウント作成
2. **ログイン**: 作成したアカウントでログイン
3. **アップロード**: 画像タブで画像ファイルをアップロード
4. **設問回答**: 表示される設問に回答
5. **感情選択**: 感情候補を1つ以上選択
6. **テキスト生成**: 出力形式を選択して生成ボタン押下
7. **コピー**: コピーボタンでクリップボードにコピーされることを確認
8. **再生成**: 再生成ボタンで別の文章が生成されることを確認
9. **履歴**: /history でセッション一覧が表示されることを確認
10. **削除**: セッション削除が正常に動作することを確認

---

## クリーンアップ

```bash
docker-compose down -v  # ボリュームも削除
```
