# 自治体財産管理システム　システム設計書

行政財産使用許可 ・ 普通財産貸付 管理システム  
版数：1.3　【内部管理用・担当部署限定】　※ ローカル開発版（localhost）

| 版数 | 主な変更内容 |
|------|------------|
| v1.0 | 初版 |
| v1.1 | localhost / React + Python 固定に変更 |
| v1.2 | ステータス遷移・履歴管理・計算仕様・監査ログを強化 |
| v1.3 | 更新モデル統一・is_latest追加・遷移トリガー明確化・楽観ロック追加、他 |
| v1.4 | renewal_in_progress廃止・is_latest_case追加・t_file設計統一・楽観ロック強化・リストア手順・エラー仕様・各種細則追加 |

---

## 1. システム概要

### 1.1 目的

本システムは、自治体が所有する行政財産（使用許可）および普通財産（貸付）を一元的に管理し、紙・Excelによる分散管理から脱却して業務効率化を図ることを目的とする。

### 1.2 対象ユーザー

| 区分 | 対象者 | 想定人数 |
|------|--------|----------|
| 一般ユーザー | 財産管理担当職員 | 3〜4名 |
| 管理者 | 担当係長・課長補佐 | 1名 |
| 閲覧のみ | 関連部署（監査等） | 必要に応じ |

### 1.3 対象財産

| 財産区分 | 法的根拠 | 管理内容 |
|----------|----------|----------|
| 行政財産（使用許可） | 地方自治法第238条の4 | 庁舎・公園等の一時的使用許可 |
| 普通財産（貸付） | 地方自治法第238条の5 | 土地・建物の賃貸借契約管理 |

### 1.4 システム対象範囲（スコープ）

> ⚠️ v1.2追加：「どこまでをシステムが担うか」を明示する

| 業務 | システム対象 | 備考 |
|------|------------|------|
| 申請書の受付 | **対象外**（紙運用継続） | 担当者がシステムへ転記する |
| 情報入力・案件管理 | **対象** | ステータス管理・検索・履歴保持 |
| 使用料・賃料計算 | **対象** | 自動計算ロジック（根拠も保存） |
| 決裁・押印 | **対象外**（システム外で実施） | システムはステータス変更で記録のみ |
| 許可証・契約書の作成 | **対象**（PDF生成） | 押印前のドラフトをシステムで作成 |
| 押印後の原本管理 | **対象外**（紙保管継続） | スキャンPDFを添付ファイルとして保存は可 |
| 更新通知文の作成 | **対象** | PDF生成のみ。郵送は手作業 |

### 1.5 現状課題と解決方針

| 現状課題 | 解決方針 |
|----------|----------|
| 紙・Excelでの管理によるデータ散在 | システムへの一元集約・DBでの管理 |
| 許可証・契約書の手作業作成 | テンプレートからのPDF自動生成 |
| 使用料計算のミスリスク | 計算根拠を完全保存するロジックに変更 |
| 財産情報の検索・参照が困難 | 財産台帳のデジタル化と検索機能 |
| 更新期限の見落とし | 有効期限アラート機能 |
| 変更履歴が追えない | 全テーブルに履歴管理を追加 |

---

## 2. 機能要件

### 2.1 機能一覧

| No | 機能名 | 区分 | 優先度 |
|----|--------|------|--------|
| F-01 | 財産台帳管理 | 財産管理 | 必須 |
| F-02 | 地図連携（位置情報表示） | 財産管理 | 必須 |
| F-03 | 添付ファイル管理（汎用） | 財産管理 | 必須 |
| F-04 | 使用許可申請登録・管理 | 申請管理 | 必須 |
| F-05 | 普通財産貸付登録・管理 | 申請管理 | 必須 |
| F-06 | 使用料・賃料の自動計算（根拠保存） | 料金管理 | 必須 |
| F-07 | 使用許可証PDF出力 | 帳票出力 | 必須 |
| F-08 | 土地貸付契約書PDF出力 | 帳票出力 | 必須 |
| F-09 | 建物貸付契約書PDF出力 | 帳票出力 | 必須 |
| F-10 | 更新通知文PDF出力 | 帳票出力 | 必須 |
| F-11 | 有効期限アラート | 通知 | 高 |
| F-12 | 案件検索・一覧表示（ページング付き） | 検索 | 必須 |
| F-13 | ダッシュボード | 可視化 | 高 |
| F-14 | 変更履歴表示 | 履歴 | 必須 |
| F-15 | CSVエクスポート | データ出力 | 高 |
| F-16 | 一括賃料改定 | 料金管理 | 中 |

### 2.2 財産台帳管理（F-01〜F-03）

#### 2.2.1 管理項目

| カテゴリ | 項目名 | 型 | 備考 |
|----------|--------|----|------|
| 基本情報 | 財産コード | 文字列 | システム自動採番 |
| 基本情報 | 財産名称 | 文字列 | |
| 基本情報 | 財産区分 | 選択 | 行政財産 / 普通財産 |
| 基本情報 | 所在地（住所） | 文字列 | |
| 基本情報 | 地番 | 文字列 | |
| 基本情報 | 地目 / 種別 | 選択 | 宅地・田・畑・山林 等 |
| 基本情報 | 面積（㎡） | 数値 | 小数点2位 |
| 基本情報 | 取得年月日 | 日付 | |
| 基本情報 | is_deleted | 真偽値 | 論理削除フラグ（物理削除は行わない） |
| 基本情報 | 備考 | テキスト | 自由記述 |
| 位置情報 | 緯度・経度 | 数値 | 地図連携用 |
| 添付管理 | 添付ファイル | ファイル | 汎用ファイルテーブル参照（後述） |

### 2.3 更新モデルの統一

> ⚠️ v1.3変更：使用許可と貸付で「更新」のデータモデルが二重定義になっていた問題を解消する

**採用方針：案A（両方とも新レコード＋親子関係）**

使用許可・貸付ともに、更新時は**新レコードを作成**し、`parent_case_id` で元案件と紐づける。

```
t_permission / t_lease
─────────────────────────────────────────────────
id: 1  parent_case_id: NULL  renewal_seq: 0  ← 初回
id: 5  parent_case_id: 1     renewal_seq: 1  ← 1回目更新
id: 9  parent_case_id: 1     renewal_seq: 2  ← 2回目更新（parent_case_idは常に初回IDを指す）
```

**メリット：**
- 履歴・変更が各レコードに明確に残る
- 更新回数は `renewal_seq` カラムで管理（自動連番）
- 旧案件は `expired` / `active`（延長）のままで残り検索可能

**影響する修正：**
- `t_permission` / `t_lease` に `parent_case_id`（nullable FK、自己参照）と `renewal_seq`（integer, default 0）を追加
- v1.2で `t_lease` にあった `更新回数` カラムは `renewal_seq` に統一し、両テーブルで共通化
- 更新通知文PDF生成時は、同一 `parent_case_id` チェーンの最新レコードを対象とする



> ⚠️ v1.2追加：ステータス定義と遷移ルールを明示する

#### 2.4.1 行政財産使用許可のステータス定義

> ⚠️ v1.3追加・v1.4修正：`renewal_in_progress` を廃止。元レコードは `approved`/`active` のまま維持し、更新は新レコード（`draft`）のみで表現する

| ステータス | 説明 | 遷移トリガー（誰が・何をしたとき） |
|-----------|------|---------------------------------|
| `draft` | 下書き（入力途中・未確定） | 担当者が新規登録または更新手続きを開始したとき |
| `submitted` | 申請受付済み | 担当者が入力完了し「受付登録」ボタンを押したとき |
| `under_review` | 審査中 | 担当者が「審査開始」ボタンを押したとき |
| `pending_approval` | 決裁待ち | 担当者が「決裁上申」ボタンを押したとき（紙の決裁書を上申） |
| `approved` | 決裁完了（許可証発行可能） | 管理者が「決裁完了」ボタンを押したとき（≠押印完了） |
| `issued` | 交付済み（任意） | 担当者が許可証を交付し「交付済み」ボタンを押したとき |
| `rejected` | 差戻し | 管理者が「差戻し」ボタンを押したとき（理由必須） |
| `expired` | 期間終了 | 使用期間終了日を過ぎたとき（バッチ or 手動） |
| `cancelled` | 取消 | 管理者が「取消」ボタンを押したとき（理由必須） |

> `renewal_in_progress` を廃止した理由：元レコードと新レコードの二重管理は不整合の温床になるため。更新中の状態は「新レコードの `draft`」のみで表現し、元レコードは変更しない。

> 注：`approved` は「システム上の決裁完了」を意味し、押印完了とは分離する。押印管理はシステム対象外（スコープ §1.4 参照）。`issued` は任意で追加できる軽量ステータス。

#### 2.4.2 行政財産使用許可の状態遷移ルール

```
draft
  └─(入力完了)──→ submitted
                    └─(審査開始)──→ under_review
                                      ├─(差戻し)──→ rejected
                                      │               └─(再申請)──→ submitted
                                      └─(承認)──→ pending_approval
                                                    ├─(差戻し)──→ rejected
                                                    └─(決裁完了)──→ approved
                                                                      ├─(交付)──→ issued（任意）
                                                                      ├─(期間満了)──→ expired
                                                                      └─(取消処分)──→ cancelled

【更新手続きの場合】
approved/issued/expired
  └─(更新手続き開始)──→ 新レコード(draft) ← parent_case_id に元レコードIDを設定
                            └─ 以降は通常フローと同じ
```

**遷移制約（システムで強制する）：**
- `expired` / `cancelled` からは原則戻せない（取消後の再申請は新規案件として登録）
- `approved` → `submitted` などの逆戻りは禁止
- ステータス変更時は必ず変更理由をテキスト入力させ、監査ログに記録する

#### 2.4.3 普通財産貸付のステータス定義

| ステータス | 説明 | 遷移トリガー（誰が・何をしたとき） |
|-----------|------|---------------------------------|
| `draft` | 下書き | 担当者が新規登録または更新手続きを開始したとき |
| `negotiating` | 協議中（内部調整） | 担当者が「協議開始」ボタンを押したとき |
| `pending_approval` | 決裁待ち | 担当者が「決裁上申」ボタンを押したとき |
| `active` | 契約中 | 管理者が「決裁完了」ボタンを押したとき（≠押印完了） |
| `expired` | 期間終了 | 契約終了日を過ぎたとき（バッチ or 手動） |
| `terminated` | 解約 | 管理者が「解約」ボタンを押したとき（理由必須） |

#### 2.4.4 普通財産貸付の状態遷移ルール

```
draft
  └─(協議開始)──→ negotiating
                    └─(決裁上申)──→ pending_approval
                                      ├─(差戻し)──→ negotiating
                                      └─(決裁完了・契約締結)──→ active
                                                                  ├─(期間満了)──→ expired
                                                                  └─(解約)──→ terminated

【更新手続きの場合】
active/expired
  └─(更新手続き開始)──→ 新レコード(draft) ← parent_case_id に元レコードIDを設定
                            └─ 以降は通常フローと同じ（draft→negotiating→...→active）
```


### 2.5 使用許可・貸付申請管理（F-04〜F-05）

#### 2.5.1 行政財産使用許可の管理項目

| 項目名 | 型 | 備考 |
|--------|----|------|
| 許可番号 | 文字列 | 自動採番（例：R06-使-001）`approved`時に確定。年度跨ぎ対応：`{年度2桁}-使-{3桁連番}` でリセット |
| 対象財産 | FK | `m_property.id`参照。削除時はRESTRICT |
| **parent_case_id** | FK（nullable） | 更新元案件ID（自己参照）。初回はNULL |
| **renewal_seq** | 整数 | 更新連番（初回=0、1回目更新=1…） |
| **is_latest_case** | 真偽値 | 同一 parent_case_id チェーン内の最新レコードか。新レコード作成時に旧レコードをfalseに更新 |
| 申請者氏名・法人名 | 文字列 | |
| 申請者住所 | 文字列 | |
| 使用目的 | 文字列 | |
| 使用期間（開始〜終了） | 日付 | タイムゾーン：JST固定 |
| 使用部分・面積 | 数値 | 許可対象範囲（㎡） |
| 使用料 | **INTEGER** | 円単位の整数。浮動小数点型禁止。`t_fee_detail`から算出。手入力時はoverride_flagをON |
| override_flag | 真偽値 | 手入力上書き時にON |
| override_reason | テキスト | override_flag=ONの場合は必須 |
| 許可条件・特記事項 | テキスト | |
| ステータス | 選択 | 上記ステータス定義に従う |
| 許可年月日 | 日付 | `approved`への遷移時に自動セット。JST固定 |
| is_deleted | 真偽値 | 論理削除フラグ。**管理者のみ操作可。通常運用では使わない** |
| delete_reason | テキスト | 論理削除時の理由（誤登録／無効化）。管理者限定。取消は `cancelled` ステータスで対応 |

#### 2.5.2 普通財産貸付の管理項目

| 項目名 | 型 | 備考 |
|--------|----|------|
| 契約番号 | 文字列 | 自動採番（例：R06-貸-001）`active`時に確定。年度跨ぎ対応：`{年度2桁}-貸-{3桁連番}` でリセット |
| 対象財産 | FK | `m_property.id`参照。削除時はRESTRICT |
| **parent_case_id** | FK（nullable） | 更新元案件ID（自己参照）。初回はNULL |
| **renewal_seq** | 整数 | 更新連番（初回=0、1回目更新=1…） |
| **is_latest_case** | 真偽値 | 同一 parent_case_id チェーン内の最新レコードか |
| 財産種別 | 選択 | 土地 / 建物 |
| 借受者氏名・法人名 | 文字列 | |
| 借受者住所・連絡先 | 文字列 | |
| 貸付目的 | 文字列 | |
| 契約期間（開始〜終了） | 日付 | タイムゾーン：JST固定 |
| 貸付面積・部屋番号 | 文字列 | |
| 年間賃料 | **INTEGER** | 円単位の整数。浮動小数点型禁止。`t_fee_detail`から算出 |
| override_flag | 真偽値 | 手入力上書き時にON |
| override_reason | テキスト | override_flag=ONの場合は必須 |
| 支払方法 | 選択 | 月払 / 半期払 / 年払 |
| ステータス | 選択 | 上記ステータス定義に従う |
| is_deleted | 真偽値 | 論理削除フラグ。**管理者のみ操作可。通常運用では使わない** |
| delete_reason | テキスト | 論理削除時の理由（誤登録／無効化）。管理者限定。解約は `terminated` ステータスで対応 |

### 2.6 使用料・賃料 自動計算（F-06）

> ⚠️ v1.2追加：計算仕様を厳密化する

#### 2.6.1 計算順序（厳守）

```
① 基本料金 = 単価（円/㎡/月）× 面積（㎡）× 使用月数
② 日割調整 = 端月が発生する場合、日割り計算を適用（月の暦日で除す）
③ 小計     = ① + ②
④ 減免適用 = 小計 × （1 - 減額率）　※減免なしの場合は0%
⑤ 税抜金額 = ④の結果を端数処理（円未満切り捨てを基本とする）
⑥ 消費税   = ⑤ × 税率（課税 / 非課税は案件ごとに設定）
             ※消費税の端数は円未満切り捨て
⑦ 税込合計 = ⑤ + ⑥
```

#### 2.5.2 計算パラメータ

| パラメータ | 入力方法 | 備考 |
|-----------|----------|------|
| 単価（円/㎡/月） | 手入力 or マスタ参照 | 参照した場合は適用日時点の単価をスナップショット保存 |
| 面積（㎡） | 台帳から自動引用 or 手入力 | 手入力時はoverride_flagをON |
| 使用開始日・終了日 | 日付入力 | 月数・日数はシステム計算 |
| 端月の扱い | 固定（日割り） | 暦日で除す |
| 減額率（%） | 手入力 | 0〜100%。減免理由も必須入力 |
| 課税区分 | 選択 | 課税 / 非課税 |
| 端数処理 | 固定（切り捨て） | 変更不可（条例準拠） |

#### 2.6.3 `t_fee_detail`の保存内容（計算根拠の完全保存）

> ⚠️ v1.3追加：再計算時は新レコード追加（上書き禁止）。`is_latest` で最新を識別  
> ⚠️ v1.4追加：金額カラムは全て **INTEGER（円単位）**。浮動小数点型禁止

| カラム | 型 | 内容 |
|--------|-----|------|
| id | INTEGER | PK |
| case_id | INTEGER | 案件ID（FK） |
| case_type | TEXT | `permission` / `lease` |
| **is_latest** | BOOLEAN | 最新の計算結果か（再計算時に旧レコードをfalseに更新） |
| unit_price | INTEGER | 計算時点の単価・円単位スナップショット |
| area_sqm | REAL | 計算に使用した面積（㎡、小数2位まで許容） |
| start_date / end_date | DATE | 計算対象期間（JST基準） |
| months | INTEGER | 月数（自動計算） |
| fraction_days | INTEGER | 端数日数 |
| base_amount | INTEGER | 基本料金・円単位（①） |
| fraction_amount | INTEGER | 日割調整額・円単位（②） |
| subtotal | INTEGER | 小計・円単位（③） |
| discount_rate | REAL | 減額率（0.0〜1.0） |
| discount_reason | TEXT | 減免理由 |
| discounted_amount | INTEGER | 減免後税抜金額・円単位（⑤） |
| tax_rate | REAL | 適用税率（例：0.10） |
| tax_amount | INTEGER | 消費税額・円単位（⑥） |
| total_amount | INTEGER | 税込合計・円単位（⑦） |
| calculated_at | DATETIME | 計算実行日時（JST） |
| calculated_by | INTEGER | 計算実行ユーザーID |
| formula_version | TEXT | 計算式バージョン（将来の改正に備える） |

### 2.7 PDF帳票出力（F-07〜F-10）

| 帳票名 | 対象 | 主な記載内容 |
|--------|------|-------------|
| 使用許可証 | 行政財産 | 許可番号・使用者・対象財産・期間・条件・使用料・首長印欄 |
| 土地貸付契約書 | 普通財産（土地） | 契約番号・甲乙氏名・物件表示・期間・賃料・特約・署名欄 |
| 建物貸付契約書 | 普通財産（建物） | 契約番号・甲乙氏名・物件表示・期間・賃料・特約・署名欄 |
| 更新通知文 | 両方 | 宛先・契約番号・更新期限・新期間・新賃料・手続き案内 |

**PDF生成に関する設計方針：**
- 帳票生成APIは `POST` メソッドとする（副作用として`t_document`に出力履歴を記録するため）
- 生成したPDFは `backend/generated_pdfs/` に保存し、ダウンロードURLを返す
- PDF生成を許可するステータス：`approved` / `issued` / `active` / `expired`（期間終了後の再発行需要に対応）
- `draft` / `pending_approval` / `rejected` / `cancelled` / `terminated` は生成禁止

---

## 3. 非機能要件

> ⚠️ v1.2追加：セキュリティ・ログ・バックアップ要件を強化

### 3.1 性能

| 要件 | 目標値 |
|------|--------|
| 画面表示速度 | 3秒以内（通常操作） |
| 同時接続ユーザー数 | 5名（担当部署のみ） |
| 一覧のページング | 1ページ20件。検索結果は最大500件まで |

### 3.2 セキュリティ

| 要件 | 仕様 |
|------|------|
| ログイン認証 | ID・パスワード認証（bcryptでハッシュ化） |
| パスワードポリシー | 8文字以上・英数字混在必須 |
| ログイン失敗制限 | 5回連続失敗でアカウントロック（管理者が解除） |
| セッション期限 | JWTトークン有効期限8時間（操作継続で延長なし） |
| JWTの失効管理 | ログアウト時にサーバー側のブラックリストに追加 |
| 通信 | ローカル開発はHTTP可・本番移行時にHTTPS対応 |
| 権限制御 | ロールベース（一般職員 / 管理者 / 閲覧のみ） |

### 3.3 操作ログ（監査対応）

> ⚠️ v1.2追加：before/after・フィールド単位差分を記録する

`t_audit_log` に以下を記録する：

| カラム | 内容 |
|--------|------|
| id | ログID |
| user_id | 操作ユーザーID |
| action | `CREATE` / `UPDATE` / `DELETE` / `LOGIN` / `EXPORT` / `PDF_GEN` |
| target_table | 操作対象テーブル名 |
| target_id | 操作対象レコードID |
| changed_fields | 変更フィールド一覧（JSON形式） |
| before_value | 変更前の値（JSON形式） |
| after_value | 変更後の値（JSON形式） |
| performed_at | 操作日時 |
| ip_address | クライアントIPアドレス |

### 3.4 バックアップ・リストア

> ⚠️ v1.2追加・v1.4追記：SQLiteの破損リスク対策とリストア手順を明記

**バックアップ手順：**
- SQLiteのオンラインバックアップAPIを使用する（`sqlite3 zaisan.db ".backup backup.db"`）  
  ※ ファイルコピーでは書き込み中に破損する可能性があるため禁止
- バックアップタイミング：毎日23:00（cron / Windowsタスクスケジューラー）
- 保持世代：7世代（1週間分）
- 保存場所：`backend/backups/zaisan_YYYYMMDD.db`

**リストア手順（v1.4追加）：**

```bash
# 1. アプリを停止する
#    → uvicorn プロセスを Ctrl+C または kill で停止

# 2. 現在のDBをリネームして退避
mv backend/zaisan.db backend/zaisan_broken_YYYYMMDD.db

# 3. バックアップから復元
cp backend/backups/zaisan_YYYYMMDD.db backend/zaisan.db

# 4. 整合性確認
sqlite3 backend/zaisan.db "PRAGMA integrity_check;"
# → "ok" が返れば正常

# 5. アプリを再起動
uvicorn main:app --reload --port 8000
```

> リストア後は担当者に復元日時と失われたデータ範囲を必ず連絡すること。

### 3.5 監査ログの肥大化対策（v1.4更新）

- **月次で別ファイルに退避**する（任意だが推奨）：

```bash
# 毎月1日に前月分をCSVエクスポートして退避
sqlite3 zaisan.db ".mode csv" ".output audit_2024_04.csv" \
  "SELECT * FROM t_audit_log WHERE performed_at < '2024-05-01';"

# エクスポート後、元テーブルから削除
sqlite3 zaisan.db "DELETE FROM t_audit_log WHERE performed_at < '2024-05-01';"
sqlite3 zaisan.db "VACUUM;"
```

- 退避したCSVは `backend/audit_archive/` に保管する
- 2年以上経過したアーカイブCSVは別途長期保管媒体（外部ドライブ等）に移動する

### 3.6 その他

| 要件 | 仕様 |
|------|------|
| 対応ブラウザ | Chrome / Edge（最新2世代） |
| データ保存期間 | 契約終了後10年以上（論理削除のみ・物理削除禁止） |
| 可用性 | ローカル運用のため明示的なSLAなし。PC停止時はアクセス不可 |
| **タイムゾーン** | 全日付・日時はJST（UTC+9）固定。DBにはISO 8601形式で保存（`2024-04-01T09:00:00+09:00`）。フロントエンドも同様 |
| **金額型** | 全金額カラムはINTEGER（円単位）。計算中間値もPython `decimal.Decimal` を使用し、最終結果を `int()` で整数化してから保存する |
| **CSVエクスポート文字コード** | UTF-8 BOM付き（`utf-8-sig`）。Excelで直接開けることを優先する |

### 3.7 エラーレスポンス仕様（v1.4追加）

全APIエンドポイントで以下の形式を統一する：

```json
// 成功時
{ "data": { ... }, "message": "OK" }

// エラー時
{
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "このステータスへの変更は許可されていません",
    "detail": { "current": "draft", "requested": "approved" }
  }
}
```

| HTTPコード | 用途 |
|-----------|------|
| 200 | 正常取得・更新 |
| 201 | 正常作成 |
| 400 | バリデーションエラー・不正な入力値 |
| 401 | 未認証（JWTなし・期限切れ） |
| 403 | 権限不足（ロール制限） |
| 404 | リソース未発見 |
| 409 | 楽観ロック競合・ステータス遷移違反 |
| 422 | Pydanticバリデーションエラー |
| 500 | サーバー内部エラー |

---

## 4. 画面設計（画面一覧）

| 画面ID | 画面名 | 主な機能 |
|--------|--------|----------|
| SCR-01 | ログイン画面 | ID・パスワード認証 |
| SCR-02 | ダッシュボード | 有効期限アラート・案件サマリ・ステータス別グラフ |
| SCR-03 | 財産台帳一覧 | 財産の検索・絞り込み・一覧表示（ページング付き） |
| SCR-04 | 財産台帳詳細・編集 | 基本情報・地図表示・添付ファイル・変更履歴タブ |
| SCR-05 | 財産台帳 新規登録 | 財産情報の入力・位置情報設定 |
| SCR-06 | 案件一覧（使用許可） | 許可案件の検索・ステータスフィルター（ページング付き） |
| SCR-07 | 案件登録（使用許可） | 申請情報入力・使用料自動計算・ステータス設定 |
| SCR-08 | 案件詳細（使用許可） | 許可内容確認・ステータス変更・PDF出力・変更履歴タブ |
| SCR-09 | 案件一覧（普通財産貸付） | 貸付案件の検索・ステータスフィルター（ページング付き） |
| SCR-10 | 案件登録（普通財産貸付） | 契約情報入力・賃料自動計算・ステータス設定 |
| SCR-11 | 案件詳細（普通財産貸付） | 契約内容確認・ステータス変更・PDF出力・変更履歴タブ |
| SCR-12 | マスタ管理 | 単価マスタ・ユーザー管理・テンプレート設定・アカウントロック解除 |
| SCR-13 | 一括賃料改定 | 対象案件の選択・一括改定額の入力・プレビュー・確定 |

### 4.1 ダッシュボード（SCR-02）表示要素

- 有効期限30日以内の案件アラート一覧
- 財産区分別の案件件数（行政財産 / 普通財産）
- 今月・今年度の新規許可・契約件数
- ステータス別件数グラフ
- 直近の変更履歴（監査ログから取得）

### 4.2 ステータス変更UI方針（v1.3更新）

- 案件詳細画面（SCR-08 / SCR-11）にステータス変更ボタンを配置
- **許可される遷移先のみボタンを表示**し、押せないボタンは非表示にする（不正遷移は表示しない）
- **押せない理由も明示する**：例）「審査中のため変更できません」「管理者権限が必要です」をツールチップまたはインライン表示
- ステータス変更ダイアログで変更理由を必須入力させ、楽観ロック用に現在ステータスをリクエストに含める

### 4.3 料金計算結果の表示方針（v1.3追加）

> ⚠️ 計算根拠が見えないと職員が結果を信頼できない。計算式の内訳を必ず表示する

案件登録・詳細画面（SCR-07 / SCR-08 / SCR-10 / SCR-11）の料金欄に、以下の内訳を展開表示する：

```
【使用料 計算内訳】
  単価         :  320 円/㎡/月
  面積         :  50.00 ㎡
  使用期間     :  2ヶ月 + 15日（2024/04/01 〜 2024/06/15）
  基本料金     :  32,000 円（320 × 50 × 2ヶ月）
  日割調整     :   7,741 円（320 × 50 × 15日 / 31日）
  小計         :  39,741 円
  減額（30%）  : -11,922 円（理由：福祉団体）
  税抜金額     :  27,819 円
  消費税（10%）:   2,781 円
  ────────────────────────
  税込合計     :  30,600 円
```

---

## 5. データベース設計

> ⚠️ v1.2追加：履歴管理・FK制約・論理削除・汎用ファイルテーブルを追加

### 5.1 設計方針

- **物理削除禁止**：全テーブルに `is_deleted` フラグを設け、論理削除のみ行う
- **FK制約**：参照先レコードの削除は `RESTRICT`（エラー）。案件が存在する財産は削除不可
- **履歴管理**：`t_permission` / `t_lease` / `m_property` の変更は `*_history` テーブルにスナップショット保存
- **監査ログ**：全操作を `t_audit_log` に before/after 付きで記録

### 5.2 主要テーブル一覧

| テーブル名 | 論理名 | 主な格納内容 |
|------------|--------|-------------|
| `m_property` | 財産台帳マスタ | 財産コード・名称・区分・所在・面積・緯度経度・is_deleted |
| `m_property_history` | 財産台帳変更履歴 | m_propertyのスナップショット・**operation_type**・変更日時・変更者 |
| `t_file` | 汎用添付ファイル | ファイルパス・種別・関連テーブル名・関連ID（汎用FK設計） |
| `t_permission` | 使用許可案件 | 許可番号・財産ID(FK)・申請者・期間・ステータス・parent_case_id・renewal_seq・is_deleted |
| `t_permission_history` | 使用許可変更履歴 | t_permissionのスナップショット・**operation_type**・変更日時・変更者 |
| `t_lease` | 貸付案件 | 契約番号・財産ID(FK)・借受者・期間・ステータス・parent_case_id・renewal_seq・is_deleted |
| `t_lease_history` | 貸付案件変更履歴 | t_leaseのスナップショット・**operation_type**・変更日時・変更者 |
| `t_fee_detail` | 料金計算根拠 | 単価スナップショット・面積・期間・計算式全明細・**is_latest** |
| `m_unit_price` | 単価マスタ | 財産区分・用途・単価・適用開始日・終了日（履歴保持） |
| `t_document` | 帳票出力履歴 | 案件ID・帳票種別・出力日時・出力者・ファイルパス |
| `m_user` | ユーザーマスタ | ユーザーID・氏名・役割・所属・is_locked |
| `t_jwt_blacklist` | JWTブラックリスト | 失効トークン一覧（ログアウト時に追加）・**expires_at** |
| `t_audit_log` | 操作ログ | ユーザーID・操作種別・対象・before/after・日時・IP |

### 5.3 履歴テーブルの共通仕様（v1.3追加）

> ⚠️ スナップショットだけでは「何のために変わったか」が追跡できない。`operation_type` を追加する

`m_property_history` / `t_permission_history` / `t_lease_history` に共通で以下を持つ：

| カラム | 内容 |
|--------|------|
| id | PK |
| target_id | 元レコードID（FK） |
| **operation_type** | `CREATE` / `UPDATE` / `STATUS_CHANGE` / `DELETE` / `RESTORE` |
| snapshot | 変更後のレコード全体（JSON） |
| changed_by | 操作ユーザーID |
| changed_at | 操作日時 |
| reason | 変更理由（STATUS_CHANGEの場合は必須） |

> 注：差分の詳細追跡は `t_audit_log` の `before_value` / `after_value` に任せる。履歴テーブルは「ある時点の全体像」、監査ログは「何が変わったか」と役割を分離する。audit_log を削除しても history が残るため履歴欠損リスクを低減できる。

### 5.4 汎用添付ファイルテーブル（`t_file`）

> ⚠️ v1.2変更・v1.4修正：nullable FK複数の中途半端な設計を廃止し、**完全ポリモーフィック設計**に統一する

| カラム | 内容 |
|--------|------|
| id | PK |
| **related_type** | 関連テーブル種別（`property` / `permission` / `lease`） |
| **related_id** | 関連レコードID |
| file_type | ファイル種別（`floor_plan` / `photo` / `certificate` / `contract` / `other`） |
| original_filename | アップロード時のファイル名 |
| stored_path | サーバー上の保存パス |
| file_size_bytes | ファイルサイズ |
| uploaded_at | アップロード日時（JST） |
| uploaded_by | アップロードユーザーID（FK） |
| is_deleted | 論理削除フラグ |

> 整合性の担保：DB側のFK制約は使えないため、アプリ側（FastAPIルーター）で `related_type` に応じた存在チェックを必須とする。インデックス：`(related_type, related_id)` の複合インデックスを作成する。

### 5.5 単価マスタ（`m_unit_price`）の履歴保持

条例改正時に単価を更新する際は、既存レコードの `end_date` を設定し、新レコードを追加する。
これにより、過去案件の計算根拠に影響を与えない。

```
適用開始日    | 単価      | end_date
2022-04-01   | 300円/㎡  | 2024-03-31
2024-04-01   | 320円/㎡  | NULL（現在適用中）
```

### 5.6 `t_audit_log` インデックス設計（v1.3追加）

> ⚠️ 全差分保存のため数ヶ月で肥大化する。インデックス設計を明示する

```sql
-- 必須インデックス（検索頻度が高い列）
CREATE INDEX idx_audit_log_target ON t_audit_log (target_table, target_id);
CREATE INDEX idx_audit_log_user   ON t_audit_log (user_id);
CREATE INDEX idx_audit_log_time   ON t_audit_log (performed_at);

-- 複合インデックス（案件履歴画面でよく使うクエリ用）
CREATE INDEX idx_audit_log_target_time ON t_audit_log (target_table, target_id, performed_at DESC);
```

ログのアーカイブ方針（任意・将来対応）：
- 2年以上経過した `t_audit_log` レコードは別テーブル（`t_audit_log_archive`）に移動する
- 移動後も参照は可能とし、検索UIでアーカイブも対象にできるよう設計する

---

## 6. システム構成

### 6.1 技術スタック（確定）

| レイヤー | 採用技術 | バージョン目安 | 備考 |
|----------|----------|---------------|------|
| フロントエンド | **React** | v18系 | Vite でビルド・開発サーバー起動 |
| バックエンド | **Python / FastAPI** | Python 3.11+, FastAPI 0.110+ | Uvicorn で起動 |
| データベース | SQLite | 3系 | ローカル開発。本番移行時はPostgreSQLへ切替 |
| ORM | SQLAlchemy | 2.x | マイグレーションはAlembic |
| 地図 | Leaflet.js + 国土地理院タイル | react-leaflet v4 | ライセンスフリー |
| PDF生成 | WeasyPrint（Python） | 60+ | Jinja2テンプレート → PDF（日本語：IPAexフォント指定必須） |
| ファイル保管 | ローカルディレクトリ | ― | `backend/uploads/` 配下に保存 |
| 認証 | JWT（python-jose）+ bcrypt | ― | ブラックリスト管理あり |

> ⚠️ SQLite → PostgreSQL 移行時の注意点：型差異（BOOLEAN・TIMESTAMP）・日付関数・トランザクション分離レベルを要確認。初期設計から型を標準SQLに準拠させることでリスクを低減する。

### 6.2 ローカル開発環境 構成図

```
localhost
├── :3000  React（Vite dev server）  ← ブラウザでアクセス
│              ↓ /api/* をプロキシ（vite.config.js）
└── :8000  Python FastAPI（Uvicorn） ← REST API
               ↓
           SQLite（zaisan.db）
               ↓
           uploads/          ← 添付ファイル
           generated_pdfs/   ← 生成済みPDF
           backups/          ← DBバックアップ
```

### 6.3 ディレクトリ構成

```
zaisan-kanri/
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── auth.py                   # JWT・認証ロジック
│   ├── audit.py                  # 監査ログ記録ユーティリティ
│   ├── models/
│   │   ├── property.py
│   │   ├── property_history.py
│   │   ├── permission.py
│   │   ├── permission_history.py
│   │   ├── lease.py
│   │   ├── lease_history.py
│   │   ├── fee_detail.py
│   │   ├── file.py               # 汎用添付ファイル
│   │   ├── user.py
│   │   ├── jwt_blacklist.py
│   │   └── audit_log.py
│   ├── routers/
│   │   ├── properties.py
│   │   ├── permissions.py
│   │   ├── leases.py
│   │   ├── fees.py               # 料金計算
│   │   ├── pdf.py
│   │   ├── files.py              # 添付ファイルアップロード
│   │   ├── export.py             # CSVエクスポート
│   │   └── auth.py
│   ├── schemas/
│   ├── services/
│   │   ├── fee_calculator.py     # 計算ロジック（テスト対象）
│   │   └── status_machine.py     # ステータス遷移制約
│   ├── templates/                # Jinja2 帳票テンプレート
│   ├── uploads/
│   ├── generated_pdfs/
│   ├── backups/
│   ├── zaisan.db
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Dashboard.jsx
    │   │   ├── PropertyList.jsx
    │   │   ├── PropertyDetail.jsx
    │   │   ├── PermissionList.jsx
    │   │   ├── PermissionForm.jsx
    │   │   ├── PermissionDetail.jsx
    │   │   ├── LeaseList.jsx
    │   │   ├── LeaseForm.jsx
    │   │   ├── LeaseDetail.jsx
    │   │   └── MasterAdmin.jsx
    │   ├── components/
    │   │   ├── StatusBadge.jsx
    │   │   ├── StatusTransitionButton.jsx  # 許可遷移のみ表示
    │   │   ├── FeeCalculator.jsx
    │   │   ├── HistoryTab.jsx
    │   │   └── FileUploader.jsx
    │   ├── api/
    │   └── main.jsx
    ├── package.json
    └── vite.config.js
```

### 6.4 主要 API エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/auth/login` | ログイン（JWTトークン発行） |
| POST | `/api/auth/logout` | ログアウト（JWTブラックリスト追加） |
| GET | `/api/properties` | 財産台帳一覧（クエリ：`q`, `type`, `page`, `per_page`） |
| POST | `/api/properties` | 財産台帳新規登録 |
| GET | `/api/properties/{id}` | 財産台帳詳細取得 |
| PUT | `/api/properties/{id}` | 財産台帳更新 |
| DELETE | `/api/properties/{id}` | 財産台帳論理削除（is_deleted=true） |
| GET | `/api/properties/{id}/history` | 財産台帳変更履歴取得 |
| GET | `/api/permissions` | 使用許可案件一覧（クエリ：`status`, `q`, `page`, `per_page`） |
| POST | `/api/permissions` | 使用許可案件登録 |
| GET | `/api/permissions/{id}` | 使用許可案件詳細 |
| PUT | `/api/permissions/{id}` | 使用許可案件更新 |
| DELETE | `/api/permissions/{id}` | 使用許可案件論理削除 |
| POST | `/api/permissions/{id}/status` | ステータス変更（遷移チェック・理由必須・楽観ロック） |
| GET | `/api/permissions/{id}/history` | 使用許可変更履歴取得 |
| GET | `/api/leases` | 貸付案件一覧（クエリ：`status`, `q`, `page`, `per_page`） |
| POST | `/api/leases` | 貸付案件登録 |
| GET | `/api/leases/{id}` | 貸付案件詳細 |
| PUT | `/api/leases/{id}` | 貸付案件更新 |
| DELETE | `/api/leases/{id}` | 貸付案件論理削除 |
| POST | `/api/leases/{id}/status` | ステータス変更（遷移チェック・理由必須・楽観ロック） |
| GET | `/api/leases/{id}/history` | 貸付案件変更履歴取得 |
| POST | `/api/fees/calculate` | 使用料・賃料の計算実行（根拠をDBに保存） |
| POST | `/api/pdf/permission/{id}` | 使用許可証PDF生成（出力履歴記録） |
| POST | `/api/pdf/lease-land/{id}` | 土地貸付契約書PDF生成 |
| POST | `/api/pdf/lease-building/{id}` | 建物貸付契約書PDF生成 |
| POST | `/api/pdf/renewal/{id}` | 更新通知文PDF生成 |
| POST | `/api/files/upload` | 添付ファイルアップロード（汎用） |
| DELETE | `/api/files/{id}` | 添付ファイル論理削除 |
| GET | `/api/export/permissions` | 使用許可案件CSVエクスポート |
| GET | `/api/export/leases` | 貸付案件CSVエクスポート |
| POST | `/api/leases/bulk-update-fee` | 一括賃料改定（全成功 or 全失敗） |
| GET | `/api/dashboard/summary` | ダッシュボード集計データ |

**ステータス変更APIの楽観ロック仕様（v1.3追加・v1.4強化）：**

```json
// POST /api/permissions/{id}/status  リクエストボディ
{
  "new_status": "approved",
  "reason": "決裁完了",
  "expected_current_status": "pending_approval",
  "expected_updated_at": "2024-05-01T10:30:00+09:00"
}
```

サーバー側で以下の両方をチェックし、不一致なら `409 Conflict` を返す：
- 現在のステータス ≠ `expected_current_status`
- 最終更新日時 ≠ `expected_updated_at`

これにより、「同一案件を2人が同時に開いて操作した」ケースを確実に検知できる。

**一括賃料改定APIのトランザクション仕様（v1.3追加・v1.4上限追加）：**
- **対象案件の上限：100件まで**（SQLiteのロック時間が長くなりすぎるため。UIで件数を表示し、超える場合は警告を出す）
- 対象案件全件の更新を1トランザクションで実行する
- 1件でも失敗した場合は全件ロールバック（全成功 or 全失敗）
- 改定前の `t_fee_detail` は `is_latest=false` に更新し、新レコードを `is_latest=true` で追加する

### 6.5 ローカル起動手順

#### バックエンド（Python / FastAPI）

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs でSwagger UI確認可
```

#### フロントエンド（React / Vite）

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000 でアプリ起動
```

#### requirements.txt（主要パッケージ）

```
fastapi
uvicorn[standard]
sqlalchemy
alembic
pydantic[email]
python-jose[cryptography]
passlib[bcrypt]
python-multipart
weasyprint
jinja2
```

### 6.7 SQLite 運用設定（v1.3追加）

> ⚠️ 同時書き込みロックとファイル破損リスクへの対策

```python
# database.py - SQLite接続時に必ず設定する
from sqlalchemy import event

engine = create_engine("sqlite:///./zaisan.db", connect_args={"check_same_thread": False})

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")   # WALモード：同時読み書き性能向上・破損リスク低減
    cursor.execute("PRAGMA foreign_keys=ON")    # FK制約を有効化（SQLiteはデフォルトOFF）
    cursor.execute("PRAGMA synchronous=NORMAL") # WALモード時の推奨設定
    cursor.close()
```

定期メンテナンス（月1回程度）：
```bash
sqlite3 zaisan.db "VACUUM;"   # 断片化解消・ファイルサイズ圧縮
```

### 6.8 JWTブラックリストの定期クリーンアップ（v1.3追加）

> ⚠️ 有効期限切れのトークンは不要。放置するとt_jwt_blacklistが肥大化する

```python
# 週1回程度バッチで実行（cron or 起動時チェック）
DELETE FROM t_jwt_blacklist WHERE expires_at < NOW();
```

### 6.6 CORS設定

```python
# main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> ※ 本番移行時は `allow_origins` を実際のURLに限定すること。

---

## 7. 業務フロー

### 7.1 行政財産使用許可フロー

| 手順 | 操作 | システム上の状態 | 担当 |
|------|------|----------------|------|
| 1 | 申請書受付（紙） | ― | 担当職員 |
| 2 | システムへ申請情報入力 | `draft` | 担当職員 |
| 3 | 対象財産を財産台帳から紐付け・使用料計算実行 | `draft` | 担当職員 |
| 4 | 入力完了・受付に変更 | `submitted` | 担当職員 |
| 5 | 審査開始 | `under_review` | 担当職員 |
| 6 | 決裁上申 | `pending_approval` | 係長 |
| 7 | 決裁完了・許可確定（システム外で押印） | `approved` | 管理者 |
| 8 | 使用許可証PDFを生成・印刷・交付 | `issued`（任意） | 担当職員 |
| 9 | 期限30日前にダッシュボードのアラートで確認 | ― | 担当職員 |
| 10 | **更新手続き開始 → 新レコード（draft）を作成**（parent_case_id に現行案件IDを設定） | 新：`draft` | 担当職員 |
| 11 | 以降は手順2〜8と同様 | | |

### 7.2 普通財産貸付フロー

| 手順 | 操作 | システム上の状態 | 担当 |
|------|------|----------------|------|
| 1 | 貸付協議・下書き作成 | `draft` | 担当職員 |
| 2 | 内部調整・賃料計算実行 | `negotiating` | 担当職員 |
| 3 | 決裁上申 | `pending_approval` | 係長 |
| 4 | 決裁完了・契約締結（システム外で押印） | `active` | 管理者 |
| 5 | 土地 or 建物貸付契約書PDF生成・交付 | ― | 担当職員 |
| 6 | 期限30日前に更新案内メモ（ダッシュボードのアラート） | ― | システム検知→担当職員 |
| 7 | **更新手続き開始 → 新レコード（draft）を作成**（parent_case_id に現行案件IDを設定） | 新：`draft` | 担当職員 |
| 8 | 賃料計算・協議・決裁（手順2〜4と同様） | `negotiating` → `active` | 担当職員・管理者 |
| 9 | 更新通知文PDFを生成・郵送 | ― | 担当職員 |

---

## 8. 想定開発スケジュール

| フェーズ | 内容 | 期間（目安） |
|----------|------|-------------|
| Phase 0：ローカル環境構築 | Python/FastAPI・React/Vite セットアップ、DB初期化、CORS確認、WeasyPrintフォント設定 | 1〜2日 |
| Phase 1：認証・共通基盤 | JWT認証・ログアウト・ロール制御・監査ログ基盤・ステータスマシン実装 | 1〜2週間 |
| Phase 2：財産台帳CRUD | 財産台帳の登録・編集・一覧（ページング）・詳細・地図表示・履歴タブ | 2〜3週間 |
| Phase 3：案件管理CRUD | 使用許可・貸付の登録・編集・ステータス変更・料金計算根拠保存 | 3〜4週間 |
| Phase 4：PDF帳票・添付 | WeasyPrint＋Jinja2テンプレートで4種帳票実装・汎用ファイルアップロード | 2〜3週間 |
| Phase 5：ダッシュボード・エクスポート | 期限アラート・集計グラフ・CSVエクスポート | 1〜2週間 |
| Phase 6：テスト・調整 | 動作確認・データ投入・UI修正・バックアップ手順確認 | 1〜2週間 |

> ※ 合計約3〜4ヶ月（担当者1〜2名での内製開発目安）

---

## 9. 課題・リスク・今後の検討事項

| 区分 | 内容 | 対応方針 |
|------|------|----------|
| リスク | 既存Excelデータの移行精度 | 移行チェックリストを作成・担当者が目視確認 |
| リスク | LGWAN環境での地図表示制約 | 国土地理院タイルで代替（gov.go.jp、ライセンスフリー）・要事前確認 |
| リスク | ローカルPCの障害によるDBファイル消失 | SQLite公式バックアップAPIを使用・週次で外部ドライブへ複製・§3.4のリストア手順で対応 |
| リスク | WeasyPrintの日本語フォント崩れ | IPAexフォントを明示指定・Phase 0の環境構築手順に含める |
| リスク | SQLite→PostgreSQL移行時の型差異 | 初期から標準SQL型を使用・BOOLEAN/TIMESTAMPをSQLiteでも明示管理 |
| リスク | 一括賃料改定のロック時間 | 対象100件上限・UIで警告表示 |
| 課題 | 帳票テンプレートの自治体固有化 | 要件定義時に実際の様式を収集しJinja2テンプレートへ反映 |
| 課題 | 条例改正時の単価マスタ更新手順 | 管理者画面から職員が更新（end_date設定＋新レコード追加） |
| 課題 | 監査ログの肥大化 | §3.5の月次CSV退避手順で対応 |
| 今後 | ローカル→サーバー移行 | SQLiteをPostgreSQLに切り替え・Docker化を検討 |
| 今後 | 電子申請窓口との連携 | サーバー移行後に別途検討 |
| 今後 | メール通知（更新期限） | サーバー化後にSMTP連携を追加 |
| 今後 | 他部署への展開・マルチテナント化 | 利用実績を踏まえて判断 |
