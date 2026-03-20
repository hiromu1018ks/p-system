import { test, expect } from '../fixtures/auth.js';

test.describe('ダッシュボード', () => {
  test('ダッシュボード表示', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');
    await adminPage.waitForLoadState('networkidle');

    // Check all 4 KPI cards exist
    await expect(adminPage.getByText('使用許可案件中')).toBeVisible();
    await expect(adminPage.getByText('貸付案件中')).toBeVisible();
    await expect(adminPage.getByText('期限切れ間近')).toBeVisible();
    await expect(adminPage.getByText('今月新規')).toBeVisible();
  });

  test('ステータスチャート表示', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.getByText('ステータス別件数')).toBeVisible();
  });

  test('有効期限アラート表示', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');
    await adminPage.waitForLoadState('networkidle');

    // Section should exist (may be empty or have alerts)
    await expect(adminPage.getByText('有効期限アラート')).toBeVisible();
  });

  test('最近の操作履歴表示', async ({ adminPage }) => {
    await adminPage.goto('/dashboard');
    await adminPage.waitForLoadState('networkidle');

    await expect(adminPage.getByText('最近の操作履歴')).toBeVisible();
  });
});
