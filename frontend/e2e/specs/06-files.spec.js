import { test, expect } from '../fixtures/auth.js';
import { api } from '../helpers/api.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

test.describe('ファイル管理', () => {
  let token, propertyId, permissionId, leaseId;
  const testFilePath = path.join(__dirname, '..', 'test-data', 'test-upload.txt');

  test.beforeAll(async () => {
    // Create test file
    fs.mkdirSync(path.dirname(testFilePath), { recursive: true });
    fs.writeFileSync(testFilePath, 'E2Eテストファイル内容\n');

    const loginData = await api.login('admin', 'Admin123');
    token = loginData.access_token;

    const prop = await api.createProperty(token, { name: 'ファイルテスト財産', property_type: 'administrative' });
    propertyId = prop.id;

    const perm = await api.createPermission(token, {
      property_id: propertyId, applicant_name: 'ファイル申請者', applicant_address: 'テスト',
      purpose: 'ファイルテスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    permissionId = perm.id;

    const lease = await api.createLease(token, {
      property_id: propertyId, property_sub_type: 'land', lessee_name: 'ファイル借受者',
      lessee_address: 'テスト', purpose: 'ファイルテスト', start_date: '2025-04-01', end_date: '2026-03-31',
    });
    leaseId = lease.id;
  });

  test('物件へのファイルアップロード', async ({ adminPage }) => {
    await adminPage.goto(`/properties/${propertyId}`);
    await adminPage.waitForLoadState('networkidle');

    // Switch to files tab
    await adminPage.getByRole('button', { name: '添付ファイル' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Initially empty
    await expect(adminPage.getByText('添付ファイルはありません')).toBeVisible();

    // Upload file
    const fileInput = adminPage.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);
    await adminPage.waitForLoadState('networkidle');

    // File should appear in list
    await expect(adminPage.getByText('test-upload.txt')).toBeVisible();
  });

  test('許可へのファイルアップロード', async ({ adminPage }) => {
    await adminPage.goto(`/permissions/${permissionId}`);
    await adminPage.waitForLoadState('networkidle');

    await adminPage.getByRole('button', { name: '添付ファイル' }).click();
    await adminPage.waitForLoadState('networkidle');

    const fileInput = adminPage.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.getByText('test-upload.txt')).toBeVisible();
  });

  test('賃貸借へのファイルアップロード', async ({ adminPage }) => {
    await adminPage.goto(`/leases/${leaseId}`);
    await adminPage.waitForLoadState('networkidle');

    await adminPage.getByRole('button', { name: '添付ファイル' }).click();
    await adminPage.waitForLoadState('networkidle');

    const fileInput = adminPage.locator('input[type="file"]');
    await fileInput.setInputFiles(testFilePath);
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.getByText('test-upload.txt')).toBeVisible();
  });

  test('ファイル削除', async ({ adminPage }) => {
    // Upload via API first
    const files = await api.uploadFile(token, testFilePath, 'property', propertyId);

    await adminPage.goto(`/properties/${propertyId}`);
    await adminPage.waitForLoadState('networkidle');

    await adminPage.getByRole('button', { name: '添付ファイル' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Delete the file
    adminPage.once('dialog', dialog => dialog.accept());
    await adminPage.getByRole('button', { name: '削除' }).first().click();
    await adminPage.waitForLoadState('networkidle');

    // Verify file is gone (might show empty message or just not show the file)
    const fileVisible = await adminPage.getByText('test-upload.txt').isVisible().catch(() => false);
    expect(fileVisible).toBe(false);
  });
});
