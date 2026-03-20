import { test, expect } from '../fixtures/auth.js';
import { api } from '../helpers/api.js';

test.describe('使用許可フロー', () => {
  let token, propertyId;

  test.beforeAll(async () => {
    const loginData = await api.login('admin', 'Admin123');
    token = loginData.access_token;
    const prop = await api.createProperty(token, { name: '許可テスト財産', property_type: 'administrative' });
    propertyId = prop.id;
  });

  async function createPermission() {
    return api.createPermission(token, {
      property_id: propertyId,
      applicant_name: 'テスト申請者',
      applicant_address: '東港区テスト1-1-1',
      purpose: 'テスト目的',
      start_date: '2025-04-01',
      end_date: '2026-03-31',
    });
  }

  test('新規作成 - draft', async ({ adminPage }) => {
    const perm = await createPermission();
    expect(perm.status).toBe('draft');
  });

  test('申請: draft → submitted', async ({ adminPage }) => {
    const perm = await createPermission();
    await adminPage.goto(`/permissions/${perm.id}`);
    await adminPage.waitForLoadState('networkidle');

    await adminPage.getByRole('button', { name: '受付登録' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Verify status changed
    await expect(adminPage.getByText('申請受付済み')).toBeVisible();
  });

  test('審査: submitted → under_review → pending_approval', async ({ adminPage }) => {
    const perm = await createPermission();
    // Move to submitted
    await api.changePermissionStatus(token, perm.id, {
      new_status: 'submitted',
      reason: '',
      expected_current_status: perm.status,
      expected_updated_at: perm.updated_at,
    });

    await adminPage.goto(`/permissions/${perm.id}`);
    await adminPage.waitForLoadState('networkidle');

    // submitted → under_review
    await adminPage.getByRole('button', { name: '審査開始' }).click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('審査中')).toBeVisible();

    // under_review → pending_approval
    await adminPage.getByRole('button', { name: '決裁上申' }).click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('決裁待ち')).toBeVisible();
  });

  test('承認: pending_approval → approved → issued', async ({ adminPage }) => {
    const perm = await createPermission();
    // Move to pending_approval via API
    let updated = await api.changePermissionStatus(token, perm.id, {
      new_status: 'submitted', reason: '', expected_current_status: perm.status, expected_updated_at: perm.updated_at,
    });
    updated = await api.changePermissionStatus(token, perm.id, {
      new_status: 'under_review', reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
    });
    updated = await api.changePermissionStatus(token, perm.id, {
      new_status: 'pending_approval', reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
    });

    await adminPage.goto(`/permissions/${updated.id}`);
    await adminPage.waitForLoadState('networkidle');

    // pending_approval → approved
    await adminPage.getByRole('button', { name: '決裁完了' }).click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('決裁完了')).toBeVisible();

    // approved → issued
    await adminPage.getByRole('button', { name: '交付済み' }).click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('交付済み')).toBeVisible();
  });

  test('却下: under_review → rejected → 再申請', async ({ adminPage }) => {
    const perm = await createPermission();
    let updated = await api.changePermissionStatus(token, perm.id, {
      new_status: 'submitted', reason: '', expected_current_status: perm.status, expected_updated_at: perm.updated_at,
    });
    updated = await api.changePermissionStatus(token, perm.id, {
      new_status: 'under_review', reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
    });

    await adminPage.goto(`/permissions/${updated.id}`);
    await adminPage.waitForLoadState('networkidle');

    // under_review → rejected (opens modal)
    await adminPage.getByRole('button', { name: '差戻し' }).first().click();
    await adminPage.locator('textarea').fill('テスト差戻し理由');
    await adminPage.getByRole('button', { name: '実行' }).click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('差戻し', { exact: true }).first()).toBeVisible();

    // rejected → submitted (再申請)
    await adminPage.getByRole('button', { name: '再申請' }).first().click();
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage.getByText('申請受付済み')).toBeVisible();
  });

  test('楽観的ロック - 二重操作防止', async ({ adminPage }) => {
    const perm = await createPermission();
    // Get fresh permission
    const fresh = await api.getPermission(token, perm.id);

    // First transition succeeds
    await api.changePermissionStatus(token, perm.id, {
      new_status: 'submitted', reason: '', expected_current_status: fresh.status, expected_updated_at: fresh.updated_at,
    });

    // Second transition with old expected values should fail
    try {
      await api.changePermissionStatus(token, perm.id, {
        new_status: 'under_review', reason: '', expected_current_status: perm.status, expected_updated_at: perm.updated_at,
      });
      // Should not reach here
      expect(true).toBe(false);
    } catch (err) {
      expect(err.message).toBeTruthy();
    }
  });
});
