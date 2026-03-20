import { test, expect } from '../fixtures/auth.js';
import { api } from '../helpers/api.js';

test.describe('料金計算', () => {
  let token, propertyId, permissionId, leaseId;

  test.beforeAll(async () => {
    const loginData = await api.login('admin', 'Admin123');
    token = loginData.access_token;
    const prop = await api.createProperty(token, { name: '料金テスト財産', property_type: 'administrative' });
    propertyId = prop.id;

    const perm = await api.createPermission(token, {
      property_id: propertyId, applicant_name: '料金申請者', applicant_address: 'テスト住所',
      purpose: '料金テスト目的', start_date: '2025-04-01', end_date: '2026-03-31', usage_area_sqm: 100,
    });
    permissionId = perm.id;

    const lease = await api.createLease(token, {
      property_id: propertyId, property_sub_type: 'land', lessee_name: '料金借受者',
      lessee_address: 'テスト住所', purpose: '料金テスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    leaseId = lease.id;
  });

  test('使用許可の料金計算 (API)', async () => {
    const result = await api.calculateFee(token, {
      case_type: 'permission', case_id: permissionId,
      unit_price: 500, area_sqm: 100, start_date: '2025-04-01', end_date: '2026-03-31',
      tax_rate: 0.10,
    });

    // 500 * 100 * 12 = 600,000 base
    // 600,000 * 0.1 tax = 60,000
    // total = 660,000
    expect(result.base_amount).toBe(600000);
    expect(result.tax_amount).toBe(60000);
    expect(result.total_amount).toBe(660000);
    expect(result.months).toBe(12);
  });

  test('賃貸借の料金計算 (API)', async () => {
    const result = await api.calculateFee(token, {
      case_type: 'lease', case_id: leaseId,
      unit_price: 300, area_sqm: 50, start_date: '2025-04-01', end_date: '2026-03-31',
      tax_rate: 0.10,
    });

    // 300 * 50 * 12 = 180,000 base
    expect(result.base_amount).toBe(180000);
    expect(result.total_amount).toBe(198000);
  });

  test('使用許可の減額計算 (API)', async () => {
    const result = await api.calculateFee(token, {
      case_type: 'permission', case_id: permissionId,
      unit_price: 500, area_sqm: 100, start_date: '2025-04-01', end_date: '2026-03-31',
      discount_rate: 0.5, discount_reason: 'テスト減額', tax_rate: 0.10,
    });

    // 600,000 * 0.5 = 300,000 discounted
    // 300,000 * 0.1 = 30,000 tax
    // total = 330,000
    expect(result.discounted_amount).toBe(300000);
    expect(result.total_amount).toBe(330000);
  });

  test('料金明細表示 (UI - 使用許可)', async ({ adminPage }) => {
    await adminPage.goto(`/permissions/${permissionId}`);
    await adminPage.waitForLoadState('networkidle');

    // Switch to fee tab
    await adminPage.getByRole('button', { name: '料金計算' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Fill form
    await adminPage.locator('input[name="unit_price"]').fill('500');
    await adminPage.locator('input[name="area_sqm"]').fill('100');
    await adminPage.locator('input[name="start_date"]').fill('2025-04-01');
    await adminPage.locator('input[name="end_date"]').fill('2026-03-31');

    await adminPage.getByRole('button', { name: '計算', exact: true }).click();
    await adminPage.waitForLoadState('networkidle');

    // Verify result shows total
    await expect(adminPage.getByText('税込合計')).toBeVisible();
    await expect(adminPage.getByText('660,000')).toBeVisible();
  });
});
