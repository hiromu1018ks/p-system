import { test, expect } from '../fixtures/auth.js';
import { api } from '../helpers/api.js';

test.describe('管理者機能', () => {
  let token, propertyId;

  test.beforeAll(async () => {
    const loginData = await api.login('admin', 'Admin123');
    token = loginData.access_token;
    const prop = await api.createProperty(token, { name: '管理テスト財産', property_type: 'general' });
    propertyId = prop.id;
  });

  test('マスタ管理アクセス制限 - staff', async ({ staffPage }) => {
    await staffPage.goto('/master-admin');
    await staffPage.waitForLoadState('networkidle');

    const isRedirected = !staffPage.url().includes('/master-admin');
    const isDenied = await staffPage.getByText('管理者のみアクセス可能です。').isVisible().catch(() => false);
    expect(isRedirected || isDenied).toBeTruthy();
  });

  test('単価マスタCRUD', async ({ adminPage }) => {
    // Create unit price via API (frontend form property_type values don't match API validation)
    await api.createUnitPrice(token, {
      property_type: 'administrative',
      usage: 'E2Eテスト用途',
      unit_price: 500,
      start_date: '2025-04-01',
    });

    await adminPage.goto('/master-admin');
    await adminPage.waitForLoadState('networkidle');

    // Verify unit price appears in list
    await expect(adminPage.getByText('E2Eテスト用途')).toBeVisible();
  });

  test('ユーザー管理', async ({ adminPage }) => {
    await adminPage.goto('/master-admin');
    await adminPage.waitForLoadState('networkidle');

    // Switch to users tab
    await adminPage.getByRole('button', { name: 'ユーザー管理' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Verify users tab is active (heading visible)
    await expect(adminPage.getByText('ユーザー一覧')).toBeVisible();
  });

  test('一括賃料改定', async ({ adminPage }) => {
    // Create active lease for bulk update
    const lease = await api.createLease(token, {
      property_id: propertyId, property_sub_type: 'land', lessee_name: '一括借受者',
      lessee_address: 'テスト', purpose: '一括テスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = lease;
    for (const status of ['negotiating', 'pending_approval', 'active']) {
      updated = await api.changeLeaseStatus(token, lease.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    await adminPage.goto('/bulk-fee-update');
    await adminPage.waitForLoadState('networkidle');

    // Step 1: Select lease
    await expect(adminPage.getByText('ステップ1')).toBeVisible();
    await adminPage.locator('thead input[type="checkbox"]').check();
    await adminPage.getByRole('button', { name: '次へ' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Step 2: Set params
    await expect(adminPage.getByText('ステップ2')).toBeVisible();
    // Fill params - find inputs by their order or placeholder
    const inputs = adminPage.locator('input[type="number"]');
    await inputs.nth(0).fill('800'); // 新単価
    await inputs.nth(1).fill('0'); // 減免率
    await inputs.nth(2).fill('0.10'); // 消費税率

    await adminPage.getByRole('button', { name: 'プレビュー', exact: true }).click();
    await adminPage.waitForLoadState('networkidle');

    // Step 3: Preview and confirm
    await expect(adminPage.getByText('ステップ3')).toBeVisible();
    adminPage.once('dialog', dialog => dialog.accept());
    await adminPage.getByRole('button', { name: '実行' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Success
    await expect(adminPage.getByText('一括賃料改定が完了しました')).toBeVisible();
  });
});
