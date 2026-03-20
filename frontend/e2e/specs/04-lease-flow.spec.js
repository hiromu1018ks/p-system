import { test, expect } from '../fixtures/auth.js';
import { api } from '../helpers/api.js';

test.describe('賃貸借フロー', () => {
  let token, propertyId;

  test.beforeAll(async () => {
    const loginData = await api.login('admin', 'Admin123');
    token = loginData.access_token;
    const prop = await api.createProperty(token, { name: '賃貸借テスト財産', property_type: 'general' });
    propertyId = prop.id;
  });

  async function createLease() {
    return api.createLease(token, {
      property_id: propertyId,
      property_sub_type: 'land',
      lessee_name: 'テスト借受者',
      lessee_address: '東京都テスト2-2-2',
      purpose: 'テスト貸付目的',
      start_date: '2025-04-01',
      end_date: '2026-03-31',
      payment_method: 'monthly',
    });
  }

  test('新規作成 - draft', async ({ adminPage }) => {
    const lease = await createLease();
    expect(lease.status).toBe('draft');
  });

  test('協議中: draft → negotiating', async ({ adminPage }) => {
    const lease = await createLease();
    await adminPage.goto(`/leases/${lease.id}`);
    await adminPage.waitForLoadState('networkidle');

    await adminPage.getByRole('button', { name: '協議開始' }).click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('協議中')).toBeVisible();
  });

  test('承認申請: negotiating → pending_approval', async ({ adminPage }) => {
    const lease = await createLease();
    let updated = await api.changeLeaseStatus(token, lease.id, {
      new_status: 'negotiating', reason: '', expected_current_status: lease.status, expected_updated_at: lease.updated_at,
    });

    await adminPage.goto(`/leases/${updated.id}`);
    await adminPage.waitForLoadState('networkidle');

    await adminPage.getByRole('button', { name: '決裁上申' }).click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('決裁待ち')).toBeVisible();
  });

  test('契約開始: pending_approval → active', async ({ adminPage }) => {
    const lease = await createLease();
    let updated = lease;
    for (const status of ['negotiating', 'pending_approval']) {
      updated = await api.changeLeaseStatus(token, lease.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    await adminPage.goto(`/leases/${updated.id}`);
    await adminPage.waitForLoadState('networkidle');

    await adminPage.getByRole('button', { name: '決裁完了' }).click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('契約中')).toBeVisible();
  });

  test('差戻し: pending_approval → negotiating', async ({ adminPage }) => {
    const lease = await createLease();
    let updated = lease;
    for (const status of ['negotiating', 'pending_approval']) {
      updated = await api.changeLeaseStatus(token, lease.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    await adminPage.goto(`/leases/${updated.id}`);
    await adminPage.waitForLoadState('networkidle');

    await adminPage.getByRole('button', { name: '差戻し' }).first().click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('協議中')).toBeVisible();
  });

  test('解約: active → terminated', async ({ adminPage }) => {
    const lease = await createLease();
    let updated = lease;
    for (const status of ['negotiating', 'pending_approval', 'active']) {
      updated = await api.changeLeaseStatus(token, lease.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    await adminPage.goto(`/leases/${updated.id}`);
    await adminPage.waitForLoadState('networkidle');

    // 解約 opens modal
    await adminPage.getByRole('button', { name: '解約' }).first().click();
    await adminPage.locator('textarea').fill('テスト解約理由');
    await adminPage.getByRole('button', { name: '実行' }).click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('解約', { exact: true }).first()).toBeVisible();
  });

  test('楽観的ロック - 二重操作防止', async () => {
    const lease = await createLease();
    const fresh = await api.getLease(token, lease.id);

    await api.changeLeaseStatus(token, lease.id, {
      new_status: 'negotiating', reason: '', expected_current_status: fresh.status, expected_updated_at: fresh.updated_at,
    });

    try {
      await api.changeLeaseStatus(token, lease.id, {
        new_status: 'pending_approval', reason: '', expected_current_status: fresh.status, expected_updated_at: fresh.updated_at,
      });
      expect(true).toBe(false);
    } catch (err) {
      expect(err.message).toBeTruthy();
    }
  });
});
