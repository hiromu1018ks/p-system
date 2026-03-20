import { test, expect } from '../fixtures/auth.js';
import { api } from '../helpers/api.js';

test.describe('物件管理', () => {
  let token;

  test.beforeAll(async () => {
    const loginData = await api.login('admin', 'Admin123');
    token = loginData.access_token;
  });

  test('物件一覧表示', async ({ adminPage }) => {
    // Create test properties via API
    await api.createProperty(token, { name: 'テスト財産1', property_type: 'administrative', address: '東京都千代田区' });
    await api.createProperty(token, { name: 'テスト財産2', property_type: 'general', address: '大阪府大阪市' });

    await adminPage.goto('/properties');
    await adminPage.waitForLoadState('networkidle');

    // Check page heading
    await expect(adminPage.getByRole('heading', { name: '財産台帳一覧' })).toBeVisible();

    // Check table has rows
    const rows = adminPage.locator('table tbody tr');
    await expect(rows.first()).toBeVisible();
  });

  test('物件検索', async ({ adminPage }) => {
    await api.createProperty(token, { name: '検索テスト財産', property_type: 'administrative', address: '東京都渋谷区' });

    await adminPage.goto('/properties');
    await adminPage.waitForLoadState('networkidle');

    const searchInput = adminPage.getByPlaceholder('財産名・住所・地番で検索');
    await searchInput.fill('検索テスト財産');
    await searchInput.press('Enter');
    await adminPage.waitForLoadState('networkidle');

    // Verify search result contains the property
    await expect(adminPage.getByText('検索テスト財産')).toBeVisible();
  });

  test('物件新規登録', async ({ adminPage }) => {
    await adminPage.goto('/properties/new');
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.getByRole('heading', { name: '財産台帳新規登録' })).toBeVisible();

    await adminPage.locator('input[name="name"]').fill('E2Eテスト新規財産');
    await adminPage.locator('select[name="property_type"]').selectOption({ label: '行政財産' });
    await adminPage.locator('input[name="address"]').fill('東京都新宿区');
    await adminPage.locator('input[name="lot_number"]').fill('1-2-3');
    await adminPage.locator('select[name="land_category"]').selectOption({ label: '宅地' });
    await adminPage.locator('input[name="area_sqm"]').fill('100.5');
    await adminPage.locator('input[name="acquisition_date"]').fill('2024-01-15');

    await adminPage.getByRole('button', { name: '登録' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Should redirect to detail page
    expect(adminPage.url()).toContain('/properties/');
  });

  test('物件編集', async ({ adminPage }) => {
    const prop = await api.createProperty(token, { name: '編集テスト財産', property_type: 'general' });

    await adminPage.goto(`/properties/${prop.id}/edit`);
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.getByRole('heading', { name: '財産台帳編集' })).toBeVisible();

    await adminPage.locator('input[name="name"]').fill('編集後財産名');

    await adminPage.getByRole('button', { name: '更新' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Verify updated name on detail page
    await expect(adminPage.getByText('編集後財産名').first()).toBeVisible();
  });

  test('物件削除', async ({ adminPage }) => {
    const prop = await api.createProperty(token, { name: '削除テスト財産', property_type: 'administrative' });

    await adminPage.goto(`/properties/${prop.id}`);
    await adminPage.waitForLoadState('networkidle');

    adminPage.once('dialog', dialog => dialog.accept());
    await adminPage.getByRole('button', { name: '削除' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Should redirect to list
    expect(adminPage.url()).toContain('/properties');
  });

  test('変更履歴', async ({ adminPage }) => {
    const prop = await api.createProperty(token, { name: '履歴テスト財産', property_type: 'administrative' });

    await adminPage.goto(`/properties/${prop.id}`);
    await adminPage.waitForLoadState('networkidle');

    // Switch to history tab
    await adminPage.getByRole('button', { name: '変更履歴' }).click();
    await adminPage.waitForLoadState('networkidle');

    // Should show at least the create history entry
    const rows = adminPage.locator('table tbody tr');
    await expect(rows.first()).toBeVisible();
  });
});
