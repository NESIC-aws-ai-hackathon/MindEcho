# Domain Entities - Unit 1: Media Analysis

---

## Entity: MediaFile

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | メディアファイル一意識別子 |
| session_id | UUID | FK(generation_sessions.id), NOT NULL | 所属セッション |
| user_id | UUID | FK(users.id), NOT NULL | アップロードユーザー |
| media_type | Enum | NOT NULL | "image" \| "music" |
| file_name | String(255) | NOT NULL | 元ファイル名 |
| file_size | Integer | NOT NULL | ファイルサイズ（バイト） |
| mime_type | String(100) | NOT NULL | MIMEタイプ |
| s3_key | String(500) | NOT NULL, UNIQUE | S3オブジェクトキー |
| created_at | DateTime(TZ) | NOT NULL, default=now | アップロード日時 |

### S3キー命名規則
```
{media_type}/{year}/{month}/{uuid}.{ext}
例: image/2026/05/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg
    music/2026/05/f1e2d3c4-b5a6-7890-abcd-ef0987654321.mp3
```

### ビジネス制約
- 1セッションにつき1メディアファイル（1:1）
- セッションステータスが `created` の場合のみアップロード可能
- アップロード成功でセッションステータスが `media_uploaded` に遷移

---

## Entity: ImageAnalysisResult

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | 解析結果一意識別子 |
| media_id | UUID | FK(media_files.id), UNIQUE, NOT NULL | 対象メディア |
| colors | JSON (list[str]) | NOT NULL | 検出された主要色（3〜5色） |
| composition | String(500) | NOT NULL | 構図の説明 |
| mood | String(200) | NOT NULL | 全体的なムード |
| subjects | JSON (list[str]) | NOT NULL | 主要被写体 |
| atmosphere | String(500) | NOT NULL | 雰囲気の記述 |
| texture | String(300) | NOT NULL | テクスチャ特徴 |
| light_direction | String(200) | NOT NULL | 光の方向・質 |
| emotional_impression | String(500) | NOT NULL | 感情的印象の記述 |
| image_category | String(100) | NOT NULL | 画像種別（photograph / painting / illustration / digital_art / other） |
| style_characteristics | String(500) | NOT NULL | 種別に応じた詳細な様式・画風特徴 |
| raw_response | Text | NOT NULL | Bedrock生レスポンス（デバッグ用） |
| created_at | DateTime(TZ) | NOT NULL, default=now | 解析実行日時 |

### 解析項目（拡張10項目）
1. **colors** — 画像に含まれる主要色（例: 「深い紺色」「暖かいオレンジ」）
2. **composition** — 構図パターン（例: 「三分割構図、左寄り配置」）
3. **mood** — 全体ムード（例: 「静寂」「活力」「憂鬱」）
4. **subjects** — 被写体（例: 「山」「湖」「一人の人物」）
5. **atmosphere** — 雰囲気記述（例: 「夕暮れの静かな郊外、時間が止まったような」）
6. **texture** — テクスチャ（例: 「滑らか」「粒子感のある」「柔らかいボケ」）
7. **light_direction** — 光（例: 「逆光、左上からの自然光」）
8. **emotional_impression** — 感情的印象（例: 「見る者に懐かしさと切なさを同時に感じさせる」）
9. **image_category** — 画像種別の分類
   - `photograph`: 写真（スナップ、風景、ポートレート等）
   - `painting`: 絵画（油彩、水彩、アクリル等）
   - `illustration`: イラスト（アニメ調、手描き、ベクター等）
   - `digital_art`: デジタルアート（CG、AI生成、コンセプトアート等）
   - `other`: その他（図表、スクリーンショット、抽象画等）
10. **style_characteristics** — 種別に応じた詳細な様式・画風特徴
   - 写真の場合: 「ポートレート写真、浅い被写界深度、自然光」「街角スナップ、モノクロ」
   - 絵画の場合: 「バロック様式、明暗法」「印象派、筆タッチが残る」「ロマン主義、劇的な構図」
   - イラストの場合: 「アニメ調、セルシェード」「水彩風、淡い色使い」「厚塗り、重厚な質感」
   - デジタルアートの場合: 「CGレンダリング、フォトリアル」「グリッチアート、レトロ」

---

## Entity: MusicAnalysisResult

### 属性定義

| 属性 | 型 | 制約 | 説明 |
|---|---|---|---|
| id | UUID | PK, NOT NULL, auto-generated | 解析結果一意識別子 |
| media_id | UUID | FK(media_files.id), UNIQUE, NOT NULL | 対象メディア |
| title | String(255) | NULL | 楽曲タイトル（ID3タグ） |
| artist | String(255) | NULL | アーティスト名（ID3タグ） |
| album | String(255) | NULL | アルバム名（ID3タグ） |
| genre | String(100) | NULL | ジャンル（ID3タグ） |
| year | Integer | NULL | リリース年（ID3タグ） |
| duration_seconds | Integer | NULL | 再生時間（秒） |
| bpm | Integer | NULL | 推定BPM（テンポ数値） |
| key | String(50) | NULL | 推定キー（例: C major, A minor） |
| chord_progression | String(500) | NULL | 主要コード進行（例: I-V-vi-IV） |
| rhythm | String(200) | NOT NULL | リズム推定結果 |
| tempo | String(100) | NOT NULL | テンポ推定 |
| mood | String(200) | NOT NULL | ムード推定 |
| energy_level | String(100) | NOT NULL | エネルギーレベル |
| emotional_impression | String(500) | NOT NULL | 感情的印象の記述 |
| raw_response | Text | NOT NULL | Bedrock生レスポンス |
| created_at | DateTime(TZ) | NOT NULL, default=now | 解析実行日時 |

### メタデータ解析方式
- ID3タグ（MP3）/ Vorbis Comment（FLAC）/ AAC metadata からメタデータ抽出
- 抽出情報をテキスト化してBedrockに渡し、楽曲の印象・ムード・エネルギーを推定
- BPM・キー・コード進行はメタデータおよびジャンル情報からBedrockが推定
- メタデータが空でもファイル名＋形式から最低限の推定を実施

---

## Entity Relationships

```
┌────────────────────┐       ┌──────────────┐
│ GenerationSession  │ 1   1 │  MediaFile   │
│   (Unit 0)         ├───────►│              │
│                    │       │  session_id  │
└────────────────────┘       └──────┬───────┘
                                    │
                          1         │         1
                   ┌────────────────┼────────────────┐
                   │                                  │
                   ▼                                  ▼
     ┌─────────────────────┐          ┌─────────────────────┐
     │ ImageAnalysisResult │          │ MusicAnalysisResult │
     │                     │          │                     │
     │  media_id (FK,UQ)   │          │  media_id (FK,UQ)   │
     └─────────────────────┘          └─────────────────────┘
```

### リレーション一覧

| 親 | 子 | カーディナリティ | 削除時 |
|---|---|---|---|
| GenerationSession | MediaFile | 1:1 | CASCADE |
| MediaFile | ImageAnalysisResult | 1:0..1 | CASCADE |
| MediaFile | MusicAnalysisResult | 1:0..1 | CASCADE |

- MediaFileは media_type に応じて ImageAnalysisResult **または** MusicAnalysisResult のいずれか1つを持つ
- 両方同時に持つことはない
