# E2E Testing Design — Playwright + Page Object Model

## Purpose

仮運用前に向けたシステム全体の動作確認をPlaywrightによるE2Eテストで網羅的に実施する。

## Scope

以下の全領域をカバーする包括的なテストスイートを作成する：

- 認証・権限制御
- 物件管理（CRUD + 検索・ページネーション）
- 使用許可フロー（全ステータス遷移）
- 賃貸借フロー（全ステータス遷移）
- 料金計算
- ファイル管理（アップロード・ダウンロード・削除）— 許可/賃貸借/物件
- PDF生成（許可書・契約書・更新通知書）
- CSV出力
- ダッシュボード
- 管理者機能（マスタ管理・ユーザー管理・一括賃料改定）
- 更新フロー（許可・賃貸借）

## Approach: Playwright + Page Object Model

Page ObjectパターンでUI操作をカプセル化し、テストはビジネスフローに集中する。データ準備にはAPIヘルパーも併用する。

## File Structure

```
frontend/
├── e2e/
│   ├── playwright.config.js      # Playwright設定
│   ├── global-setup.js           # DBリセット + seed + サーバー起動確認
│   ├── test-data/                # テスト用固定ファイル（テスト画像、期待CSV等）
│   ├── fixtures/
│   │   └── auth.js               # 認証済みbrowser context fixtures
│   ├── pages/
│   │   ├── BasePage.js           # 共通基底クラス
│   │   ├── LoginPage.js
│   │   ├── DashboardPage.js
│   │   ├── PropertyListPage.js
│   │   ├── PropertyFormPage.js
│   │   ├── PropertyDetailPage.js
│   │   ├── PermissionListPage.js
│   │   ├── PermissionFormPage.js
│   │   ├── PermissionDetailPage.js
│   │   ├── LeaseListPage.js
│   │   ├── LeaseFormPage.js
│   │   ├── LeaseDetailPage.js
│   │   ├── MasterAdminPage.js
│   │   └── BulkFeeUpdatePage.js
│   ├── helpers/
│   │   └── api.js                # バックエンドAPI直接呼び出し（データ準備用）
│   └── specs/
│       ├── 01-auth.spec.js
│       ├── 02-properties.spec.js
│       ├── 03-permission-flow.spec.js
│       ├── 04-lease-flow.spec.js
│       ├── 05-fees.spec.js
│       ├── 06-files.spec.js
│       ├── 07-pdf.spec.js
│       ├── 08-csv-export.spec.js
│       ├── 09-dashboard.spec.js
│       ├── 10-admin.spec.js
│       └── 11-renewal.spec.js
└── package.json                  # @playwright/test を追加
```

Note: `helpers/db.js` は不要と判断した。DB操作はすべて `helpers/api.js` 経由のバックエンドAPIで行い、実装の詳細に依存しないようにする。

## Infrastructure

### Server Auto-Start

`playwright.config.js` の `webServer` 配列でバックエンド(:8000)とフロントエンド(:3000)を自動起動：

```js
webServer: [
  {
    command: 'cd ../backend && source venv/bin/activate && alembic upgrade head && python seed.py && uvicorn main:app --host 127.0.0.1 --port 8000',
    port: 8000,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,  // WeasyPrint + Alembic起動が遅い可能性
  },
  {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  }
]
```

- 開発中: `reuseExistingServer: true` で既に起動済みのサーバーを再利用
- CI: 毎回起動、venv activationをcommandに含める
- ヘルスチェック: Playwrightのデフォルト（HTTP GETで200応答を確認）

### Test Database Isolation

テスト用DB切り替えは**バックエンド側で環境変数対応**が必要（既存コードの変更を伴う）：

1. バックエンドのDB接続部分で `DATABASE_URL` 環境変数を参照（未設定時は既存 `zaisan.db` を使用）
2. `playwright.config.js` の `webServer` command内で環境変数を設定:
   ```bash
   DATABASE_URL=test_zaisan.db python seed.py && DATABASE_URL=test_zaisan.db uvicorn main:app ...
   ```
3. `global-setup.js` でテストDB初期化:
   - `test_zaisan.db` が存在すれば削除
   - `DATABASE_URL=test_zaisan.db alembic upgrade head`
   - `DATABASE_URL=test_zaisan.db python seed.py`
4. 各テストファイルは独立して実行可能（テスト間でDB状態に依存しない）

### Authentication Fixtures

`fixtures/auth.js` でadmin/staff/viewerそれぞれの認証済みbrowser contextを提供：

1. APIで `POST /api/auth/login` → JWT取得
2. `context.addInitScript()` で `sessionStorage` にtokenを注入
3. 認証済みのpageをテストに渡す

ログイン画面のUIテストは `01-auth.spec.js` で別途UI操作で検証。

## Selector Strategy

優先度順:

1. `data-testid` 属性（必要な箇所に最小限追加）
2. `aria-label` / `role`
3. 表示テキスト (`getByText`, `getByRole`)

避ける: CSSクラス名、DOM構造に依存するセレクタ

### data-testid 追加方針

Page Object実装時に各コンポーネントに必要な `data-testid` を**インクリメンタルに追加**する。以下の基準で追加箇所を決定：

- **フォーム入力**: `data-testid="form-field-name"` (例: `data-testid="property-name"`)
- **送信ボタン**: `data-testid="submit-btn"`
- **テーブル行**: `data-testid="row-{id}"` または `data-testid="row-{index}"`
- **ステータスバッジ**: `data-testid="status-badge"`
- **ナビゲーションリンク**: `data-testid="nav-{item}"` (例: `data-testid="nav-dashboard"`)
- **重要なアクション**: `data-testid="action-{name}"` (例: `data-testid="action-export-csv"`)

追加は各Page Objectの実装時に対応するコンポーネントに対して行い、既存の動作に影響しないHTML属性の追加のみとする。

## Page Objects

### BasePage

すべてのPage Objectの共通基底クラス:

- `page` — Playwright Page
- `waitForLoad()` — `page.waitForLoadState('networkidle')` でネットワークアイドルを待機。ページによっては追加で特定要素の出現を待つ（オーバーライド可能）
- `getFlashMessage()` — `[data-testid="flash-message"]` または `.toast` / `.alert` 要素のテキストを取得
- `assertUrl(path)` — `page.url()` が期待パスを含むことを検証

### LoginPage

- `login(username, password)` — フォーム入力 + 送信 + ダッシュボード遷移待ち
- `getErrorMessage()` — エラーメッセージ取得
- `isLocked()` — アカウントロック状態の検証

### DashboardPage

- `getKpiValues()` — 4つのKPIカード値を取得
- `getExpiryAlerts()` — 期限警告リストを取得
- `getRecentLogs()` — 最近の監査ログを取得

### PropertyListPage / PropertyFormPage / PropertyDetailPage

- `PropertyListPage`: `search(query)`, `filterByType(type)`, `clickProperty(index)`, `clickNew()`, `getRowCount()`
- `PropertyFormPage`: `fillForm(data)`, `submit()`, `assertFieldError(field)`
- `PropertyDetailPage`: `getInfo()`, `clickEdit()`, `clickDelete()`, `switchTab(tab)`, `getHistory()`, `uploadFile(path)`, `getFiles()`

### PermissionListPage / PermissionFormPage / PermissionDetailPage

- `PermissionListPage`: `filterByStatus(status)`, `clickPermission(index)`, `clickNew()`, `exportCsv()`
- `PermissionFormPage`: `fillForm(data)`, `submit()`
- `PermissionDetailPage`: `getStatus()`, `transitionTo(status)`, `calculateFee()`, `getFeeDetails()`, `generatePermissionPdf()`, `generateRenewalPdf(caseType)`, `getFiles()`, `getHistory()`

### LeaseListPage / LeaseFormPage / LeaseDetailPage

- `LeaseListPage`: `filterByStatus(status)`, `clickLease(index)`, `clickNew()`, `exportCsv()`
- `LeaseFormPage`: `fillForm(data)`, `submit()`
- `LeaseDetailPage`: `getStatus()`, `transitionTo(status)`, `calculateFee()`, `generateLandLeasePdf()`, `generateBuildingLeasePdf()`, `generateRenewalPdf()`, `getFiles()`, `getHistory()`

### MasterAdminPage / BulkFeeUpdatePage

- `MasterAdminPage`: `switchTab(tab)`, `createUnitPrice(data)`, `editUnitPrice(id, data)`, `createUser(data)`, `unlockUser(id)`
- `BulkFeeUpdatePage`: `selectLeases(ids)`, `setParams(data)`, `getPreview()`, `confirm()`

## API Helper (`helpers/api.js`)

テストデータの事前準備用。バックエンドAPIを直接HTTP呼び出しする。

```js
// 認証
api.login(username, password)           // → { access_token, user }
api.logout(token)                       // POST /api/auth/logout

// 物件
api.createProperty(token, data)         // POST /api/properties
api.getProperty(token, id)              // GET /api/properties/{id}
api.deleteProperty(token, id)           // DELETE /api/properties/{id}

// 使用許可
api.createPermission(token, data)       // POST /api/permissions
api.getPermission(token, id)            // GET /api/permissions/{id}
api.changePermissionStatus(token, id, body) // POST /api/permissions/{id}/status
api.startPermissionRenewal(token, id)   // POST /api/permissions/{id}/renewal

// 賃貸借
api.createLease(token, data)            // POST /api/leases
api.getLease(token, id)                 // GET /api/leases/{id}
api.changeLeaseStatus(token, id, body)  // POST /api/leases/{id}/status
api.startLeaseRenewal(token, id)        // POST /api/leases/{id}/renewal

// 料金
api.calculateFee(token, caseType, caseId, params) // POST /api/fees/calculate
api.getFeeDetails(token, caseType, caseId)        // GET /api/fees/{caseType}/{caseId}

// 単価マスタ
api.getUnitPrices(token)                // GET /api/unit-prices
api.createUnitPrice(token, data)        // POST /api/unit-prices

// PDF
api.generatePermissionPdf(token, id)    // POST /api/pdf/permission/{id}
api.generateLandLeasePdf(token, id)     // POST /api/pdf/lease-land/{id}
api.generateBuildingLeasePdf(token, id) // POST /api/pdf/lease-building/{id}
api.generateRenewalPdf(token, caseType, caseId) // POST /api/pdf/renewal/{caseType}/{caseId}
api.downloadPdf(token, documentId)      // GET /api/pdf/download/{documentId}

// ファイル
api.uploadFile(token, file, relatedType, relatedId) // POST /api/files/upload
api.getFiles(token, relatedType, relatedId)          // GET /api/files
```

実装は `fetch()` で直接バックエンドの `http://127.0.0.1:8000` にリクエストを送信する。Playwrightのブラウザとは独立したNode.jsコンテキストで実行される。

## Seed Data State

`global-setup.js` で `seed.py` 実行後のDB状態（テストが前提としてよいデータ）：

### ユーザー

| username | password | role | department |
|----------|----------|------|------------|
| admin | Admin123 | admin | 財政課 |
| tanaka | Tanaka123 | staff | 財産管理担当 |
| sato | Sato12345 | viewer | 監査室 |

### その他

- `seed.py` が作成する物件・許可・賃貸借の具体的な件数とステータスは、実装時に `seed.py` の内容を確認してダッシュボードテストの期待値を決定する
- ダッシュボードのKPI期待値はseedデータに基づいて固定値としてハードコードする（seed内容が変わればテストも更新）

## Test Suites

### 01-auth.spec.js — 認証・権限制御

| Test | Description |
|------|-------------|
| 正常ログイン | admin/staff/viewerでログイン → ダッシュボード表示 |
| 無効な認証情報 | 誤ったパスワード → エラーメッセージ表示 |
| アカウントロック | 5回連続失敗 → ロックメッセージ |
| ログアウト | ログアウト → ログイン画面にリダイレクト |
| セッション期限切れ | 無効なtokenをsessionStorageに設定してページアクセス → ログイン画面にリダイレクト |
| viewer制限 | viewerで `/master-admin` にアクセス → ダッシュボードにリダイレクト |
| viewer制限 | viewerで `/bulk-fee-update` にアクセス → ダッシュボードにリダイレクト |

### 02-properties.spec.js — 物件管理

| Test | Description |
|------|-------------|
| 物件一覧表示 | ページネーション、件数表示 |
| 物件検索 | キーワード検索、タイプフィルタ |
| 物件新規登録 | 全フィールド入力 → 登録成功 → 詳細画面表示 |
| 物件編集 | 既存物件を編集 → 保存成功 |
| 物件削除 | 論理削除 → 一覧に表示されない |
| 変更履歴 | CRUD操作後に履歴が記録される |

### 03-permission-flow.spec.js — 使用許可フロー

| Test | Description |
|------|-------------|
| 新規作成 | draft状態で作成 |
| 申請 | draft → submitted |
| 審査 | submitted → under_review → pending_approval |
| 承認 | pending_approval → approved |
| 発行 | approved → issued |
| 却下 | under_review → rejected → 再申請 |
| キャンセル | draft/submittedのキャンセル |
| 楽観的ロック | 二重操作の防止 |

### 04-lease-flow.spec.js — 賃貸借フロー

| Test | Description |
|------|-------------|
| 新規作成 | draft状態で作成 |
| 交渉中 | draft → negotiating |
| 承認申請 | negotiating → pending_approval |
| 契約開始 | pending_approval → active |
| 差戻し | pending_approval → negotiating |
| 解約 | active → terminated |
| 楽観的ロック | 二重操作の防止 |

### 05-fees.spec.js — 料金計算

| Test | Description |
|------|-------------|
| 使用許可の料金計算 | 7ステップ計算の結果が正しい |
| 賃貸借の料金計算 | 単価マスタ参照 + 面積・月数で計算 |
| 料金明細表示 | 計算結果が画面に正しく表示される |

### 06-files.spec.js — ファイル管理

| Test | Description |
|------|-------------|
| 許可へのファイルアップロード | 使用許可にファイル添付 → 一覧に表示 |
| 賃貸借へのファイルアップロード | 賃貸借にファイル添付 → 一覧に表示 |
| 物件へのファイルアップロード | 物件にファイル添付 → 一覧に表示 |
| ファイルダウンロード | ダウンロードが正常に完了する |
| ファイル削除 | 論理削除 → 一覧から消える |

### 07-pdf.spec.js — PDF生成

| Test | Description |
|------|-------------|
| 使用許可許可書PDF | issued状態で生成 → `POST /api/pdf/permission/{id}` → ダウンロード成功 |
| 土地賃貸借契約書PDF | active状態で生成 → `POST /api/pdf/lease-land/{id}` → ダウンロード成功 |
| 建物賃貸借契約書PDF | active状態で生成 → `POST /api/pdf/lease-building/{id}` → ダウンロード成功 |
| 更新通知書PDF | 更新記録で生成 → `POST /api/pdf/renewal/{case_type}/{case_id}` → ダウンロード成功 |
| PDF履歴 | `GET /api/pdf/history/{case_type}/{case_id}` で生成履歴が正しく記録される |

### 08-csv-export.spec.js — CSV出力

| Test | Description |
|------|-------------|
| 使用許可CSV | 一覧画面からCSVエクスポート → 内容検証 |
| 賃貸借CSV | 一覧画面からCSVエクスポート → 内容検証 |

Note: CSVエクスポートは `frontend/src/api/` モジュールではなく、コンポーネント内で直接 `window.open()` または `fetch()` を呼び出している。E2Eテストではダウンロードイベントを捕捉して内容を検証する。

### 09-dashboard.spec.js — ダッシュボード

| Test | Description |
|------|-------------|
| KPI表示 | 4つのKPIカードの値が正しい（seedデータに基づく固定期待値） |
| ステータスチャート | グラフが表示される |
| 期限警告 | 期限切れ間近の案件が表示される |
| 監査ログ | 最近の操作ログが表示される |

### 10-admin.spec.js — 管理者機能

| Test | Description |
|------|-------------|
| マスタ管理アクセス制限 | viewer/staffは `/master-admin` にアクセス → ダッシュボードにリダイレクト |
| 単価マスタCRUD | 単価の作成・編集 |
| ユーザー管理 | ユーザー一覧・作成・アンロック |
| 一括賃料改定 | 3ステップウィザード → プレビュー → 確定 |

### 11-renewal.spec.js — 更新フロー

| Test | Description |
|------|-------------|
| 使用許可の更新 | 更新開始 → 新規レコード作成 → parent_case_idリンク |
| 賃貸借の更新 | 更新開始 → 新規レコード作成 → parent_case_idリンク |
| 更新通知書PDF | 更新後に `POST /api/pdf/renewal/{case_type}/{case_id}` でPDF生成可能 |

## Test Timeouts & Configuration

- デフォルトテストタイムアウト: 30秒（Playwrightデフォルト）
- PDF生成テスト: 60秒（WeasyPrintの初回起動は遅い可能性があるため）
- `playwright.config.js` で個別テストにタイムアウト設定可能:
  ```js
  test.setTimeout(60_000);  // PDF関連テスト
  ```
- リトライ: CI環境でのみ `retries: 1` を設定。ローカルではリトライなし（失敗を即座に確認するため）

## Dependencies

- `@playwright/test` — Playwright本体
- Playwrightブラウザバイナリ（`npx playwright install chromium`）

## Commands

```bash
# Install
cd frontend && npm install -D @playwright/test && npx playwright install chromium

# Run all tests
npx playwright test

# Run with UI (debugging)
npx playwright test --ui

# Run specific file
npx playwright test e2e/specs/03-permission-flow.spec.js

# Run headed (visible browser)
npx playwright test --headed

# Run specific test
npx playwright test -g "正常ログイン"
```

## Constraints

- すべてのUIテキストは日本語
- SQLite only — PostgreSQL/MySQLは対象外
- `sessionStorage` にJWTを格納（localStorageではない）
- ステータス遷移は楽観的ロック付き（`expected_current_status` + `expected_updated_at`）
- ファイルアップロード先: `backend/uploads/`
- PDF生成先: `backend/generated_pdfs/`
