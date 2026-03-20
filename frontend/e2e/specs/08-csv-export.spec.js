import { test, expect } from '../fixtures/auth.js';
import { api } from '../helpers/api.js';
import fs from 'fs';

test.describe('CSV出力', () => {
  let token, propertyId;

  test.beforeAll(async () => {
    const loginData = await api.login('admin', 'Admin123');
    token = loginData.access_token;
    const prop = await api.createProperty(token, { name: 'CSVテスト財産', property_type: 'administrative' });
    propertyId = prop.id;

    // Create test permission
    await api.createPermission(token, {
      property_id: propertyId, applicant_name: 'CSV申請者', applicant_address: 'CSV住所',
      purpose: 'CSVテスト目的', start_date: '2025-04-01', end_date: '2026-03-31',
    });

    // Create test lease
    await api.createLease(token, {
      property_id: propertyId, property_sub_type: 'land', lessee_name: 'CSV借受者',
      lessee_address: 'CSV住所', purpose: 'CSVテスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
  });

  test('使用許可CSVエクスポート', async ({ adminPage }) => {
    await adminPage.goto('/permissions');
    await adminPage.waitForLoadState('networkidle');

    const [download] = await Promise.all([
      adminPage.waitForEvent('download', { timeout: 30000 }),
      adminPage.getByRole('button', { name: 'CSVエクスポート' }).click(),
    ]);

    const path = await download.path();
    const content = fs.readFileSync(path, 'utf-8');

    // Check CSV headers
    expect(content).toContain('許可番号');
    expect(content).toContain('申請者氏名');
    expect(content).toContain('CSV申請者');
  });

  test('賃貸借CSVエクスポート', async ({ adminPage }) => {
    await adminPage.goto('/leases');
    await adminPage.waitForLoadState('networkidle');

    const [download] = await Promise.all([
      adminPage.waitForEvent('download', { timeout: 30000 }),
      adminPage.getByRole('button', { name: 'CSVエクスポート' }).click(),
    ]);

    const path = await download.path();
    const content = fs.readFileSync(path, 'utf-8');

    expect(content).toContain('契約番号');
    expect(content).toContain('借受者氏名');
    expect(content).toContain('CSV借受者');
  });
});
