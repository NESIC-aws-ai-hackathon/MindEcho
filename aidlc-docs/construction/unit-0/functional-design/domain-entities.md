# Domain Entities - Unit 0: Auth & Core Infrastructure

---

## Entity: User

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | ユーザー一意識別子 |
| email | String(255) | UNIQUE, NOT NULL | メールアドレス（ログインID） |
| password_hash | String(255) | NOT NULL | bcryptハッシュ済みパスワード |
| created_at | DateTime(TZ) | NOT NULL, default=now | アカウント作成日時 |
| updated_at | DateTime(TZ) | NOT NULL, default=now | 最終更新日時 |

### ビジネス制約
- `email`: RFC 5322準拠の形式バリデーション、大文字小文字を区別しない（保存時にlowercase化）
- `password_hash`: 平文パスワードは保存しない。bcryptでハッシュ化（cost factor=12）
- 1ユーザー1メールアドレス（変更不可 — MVP scope）

### ライフサイクル
```
Created → Active → Deleted(物理削除)
```
- 作成: 登録API実行時
- 削除: アカウント削除API実行時に物理削除（関連データ全てカスケード削除）

---

## Entity: GenerationSession

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | セッション一意識別子 |
| user_id | UUID | FK(users.id), NOT NULL | 所有ユーザー |
| status | Enum | NOT NULL, default='created' | セッション状態 |
| media_type | Enum | NULL | メディア種別（image/music） |
| created_at | DateTime(TZ) | NOT NULL, default=now | セッション作成日時 |
| updated_at | DateTime(TZ) | NOT NULL, default=now | 最終更新日時 |
| completed_at | DateTime(TZ) | NULL | 完了日時 |

### ステータス遷移（6段階）

```
created → media_uploaded → questions_answered → emotions_selected → generated → completed
```

| 遷移 | トリガー | 前提条件 |
|---|---|---|
| created → media_uploaded | メディアアップロード+解析完了 | media_filesレコード存在 |
| media_uploaded → questions_answered | コンテクスト設問回答完了 | context_responsesレコード存在 |
| questions_answered → emotions_selected | 感情選択完了 | emotion_selectionsレコード存在 |
| emotions_selected → generated | 文章生成完了 | generated_textsレコード存在 |
| generated → completed | ユーザーが結果を確認/シェア | — |

### ビジネス制約
- **同時アクティブ制限**: ユーザーあたり最大1セッション（status ≠ 'completed'のセッションが存在する場合、新規作成不可）
- **逆戻り不可**: ステータスは前方遷移のみ（generated → questions_answered のような逆戻りは不可）
- **再生成**: statusが'generated'の場合のみ再生成可能（completedに遷移すると再生成不可）
- **タイムアウト**: MVPでは実装しない（将来的に24時間未操作で自動completed化を検討）

---

## Entity Relationships

```
┌──────────┐          ┌────────────────────┐
│   User   │ 1    N   │  GenerationSession │
│          ├──────────►│                    │
│  id (PK) │          │  user_id (FK)      │
│  email   │          │  status            │
│          │          │  media_type        │
└──────────┘          └─────────┬──────────┘
                                │
                    1           │ 1
                    ┌───────────┼───────────────┐
                    │           │               │
                    ▼           ▼               ▼
            ┌────────────┐ ┌──────────┐ ┌────────────┐
            │ media_files│ │ context_ │ │ emotion_   │
            │            │ │responses │ │selections  │
            └────────────┘ └──────────┘ └────────────┘
                                               │
                                               ▼
                                        ┌────────────┐
                                        │generated_  │
                                        │texts       │
                                        └────────────┘
```

### リレーション一覧

| 親エンティティ | 子エンティティ | カーディナリティ | 削除時動作 |
|---|---|---|---|
| User | GenerationSession | 1:N | CASCADE DELETE |
| GenerationSession | media_files | 1:1 | CASCADE DELETE |
| GenerationSession | context_responses | 1:N | CASCADE DELETE |
| GenerationSession | free_text_inputs | 1:1 (optional) | CASCADE DELETE |
| GenerationSession | emotion_selections | 1:N | CASCADE DELETE |
| GenerationSession | generated_texts | 1:N | CASCADE DELETE |

### カスケード削除の範囲（Unit 0が管理）
- **アカウント削除**: User → 全GenerationSession → 各セッション配下の全レコード + S3ファイル
- **セッション削除**: GenerationSession → 配下の全レコード + S3ファイル
