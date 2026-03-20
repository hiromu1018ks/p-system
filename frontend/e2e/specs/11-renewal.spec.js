import { test, expect } from '../fixtures/auth.js';
import { api } from '../helpers/api.js';

test.describe('更新フロー', () => {
  let token, propertyId;

  test.beforeAll(async () => {
    const loginData = await api.login('admin', 'Admin123');
    token = loginData.access_token;
    const prop = await api.createProperty(token, { name: '更新テスト財産', property_type: 'administrative' });
    propertyId = prop.id;
  });

  test('使用許可の更新 (API)', async () => {
    const perm = await api.createPermission(token, {
      property_id: propertyId, applicant_name: '更新申請者', applicant_address: 'テスト',
      purpose: '更新テスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = perm;
    for (const status of ['submitted', 'under_review', 'pending_approval', 'approved']) {
      updated = await api.changePermissionStatus(token, perm.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    const renewal = await api.startPermissionRenewal(token, updated.id);
    expect(renewal.parent_case_id).toBe(updated.id);
    expect(renewal.renewal_seq).toBe(1);
    expect(renewal.status).toBe('draft');
  });

  test('賃貸借の更新 (API)', async () => {
    const lease = await api.createLease(token, {
      property_id: propertyId, property_sub_type: 'land', lessee_name: '更新借受者',
      lessee_address: 'テスト', purpose: '更新テスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = lease;
    for (const status of ['negotiating', 'pending_approval', 'active']) {
      updated = await api.changeLeaseStatus(token, lease.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    const renewal = await api.startLeaseRenewal(token, updated.id);
    expect(renewal.parent_case_id).toBe(updated.id);
    expect(renewal.renewal_seq).toBe(1);
    expect(renewal.status).toBe('draft');
  });

  test('使用許可の更新 (UI)', async ({ adminPage }) => {
    const perm = await api.createPermission(token, {
      property_id: propertyId, applicant_name: 'UI更新申請者', applicant_address: 'テスト',
      purpose: 'UI更新テスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = perm;
    for (const status of ['submitted', 'under_review', 'pending_approval', 'approved']) {
      updated = await api.changePermissionStatus(token, perm.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    await adminPage.goto(`/permissions/${updated.id}`);
    await adminPage.waitForLoadState('networkidle');

    // Click renewal button (confirm dialog)
    adminPage.once('dialog', dialog => dialog.accept());
    await adminPage.getByRole('button', { name: '更新手続きを開始' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Should navigate to new renewal record
    // The URL should be /permissions/{newId} and status should be draft
    await expect(adminPage.getByText('下書き', { exact: true })).toBeVisible();
  });

  test('賃貸借の更新 (UI)', async ({ adminPage }) => {
    const lease = await api.createLease(token, {
      property_id: propertyId, property_sub_type: 'land', lessee_name: 'UI更新借受者',
      lessee_address: 'テスト', purpose: 'UI更新テスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = lease;
    for (const status of ['negotiating', 'pending_approval', 'active']) {
      updated = await api.changeLeaseStatus(token, lease.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    await adminPage.goto(`/leases/${updated.id}`);
    await adminPage.waitForLoadState('networkidle');

    adminPage.once('dialog', dialog => dialog.accept());
    await adminPage.getByRole('button', { name: '更新手続きを開始' }).click();
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.getByText('下書き', { exact: true })).toBeVisible();
  });

  test.setTimeout(60_000);

  test('更新通知書PDF生成', async () => {
    // Create permission, advance to approved, start renewal, advance renewal to approved
    const perm = await api.createPermission(token, {
      property_id: propertyId, applicant_name: '通知書申請者', applicant_address: 'テスト',
      purpose: '通知書テスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    let updated = perm;
    for (const status of ['submitted', 'under_review', 'pending_approval', 'approved']) {
      updated = await api.changePermissionStatus(token, perm.id, {
        new_status: status, reason: '', expected_current_status: updated.status, expected_updated_at: updated.updated_at,
      });
    }

    const renewal = await api.startPermissionRenewal(token, updated.id);

    // Advance renewal to approved
    let rUpdated = renewal;
    for (const status of ['submitted', 'under_review', 'pending_approval', 'approved']) {
      rUpdated = await api.changePermissionStatus(token, renewal.id, {
        new_status: status, reason: '', expected_current_status: rUpdated.status, expected_updated_at: rUpdated.updated_at,
      });
    }

    const pdf = await api.generateRenewalPdf(token, 'permission', renewal.id);
    expect(pdf.document_type).toBe('renewal_notice');
    expect(pdf.filename).toContain('.pdf');
  });
});
