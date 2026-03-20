import { test, expect } from '../fixtures/auth.js';
import LoginPage from '../pages/LoginPage.js';
import { api } from '../helpers/api.js';

// Tests 1-7 use unauthenticated pages
test.describe('認証・権限制御', () => {
  let token;

  test.beforeAll(async () => {
    const loginData = await api.login('admin', 'Admin123');
    token = loginData.access_token;
    // Create a dedicated user for lock testing
    try {
      await api.createUser(token, {
        username: 'locktest',
        password: 'LockTest123',
        display_name: 'ロックテスト',
        role: 'staff',
        department: 'テスト',
      });
    } catch {
      // User may already exist from a previous run
    }
  });

  test('正常ログイン - admin', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('admin', 'Admin123');
    expect(page.url()).toContain('/dashboard');
  });

  test('正常ログイン - staff', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('tanaka', 'Tanaka123');
    expect(page.url()).toContain('/dashboard');
  });

  test('正常ログイン - viewer', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('sato', 'Sato12345');
    expect(page.url()).toContain('/dashboard');
  });

  test('無効な認証情報', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.loginExpectError('admin', 'wrongpassword');
    expect(page.url()).toContain('/login');
  });

  test('アカウントロック', async ({ page }) => {
    const loginPage = new LoginPage(page);
    // Use dedicated locktest user to avoid affecting other tests
    for (let i = 0; i < 5; i++) {
      await loginPage.goto();
      await loginPage.loginExpectError('locktest', 'wrongpassword');
    }
    await loginPage.goto();
    await loginPage.loginExpectError('locktest', 'LockTest123');
    expect(page.url()).toContain('/login');
  });

  test('ログアウト', async ({ page }) => {
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('admin', 'Admin123');
    // サイドバーのログアウトボタン
    await page.locator('.sidebar-logout').click();
    await page.waitForURL('**/login');
    expect(page.url()).toContain('/login');
  });

  test('セッション期限切れ', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    // 無効なトークンを設定
    await context.addInitScript(() => {
      sessionStorage.setItem('access_token', 'invalid-token-12345');
    });
    await page.goto('/dashboard');
    await page.waitForURL('**/login', { timeout: 10000 }).catch(() => {});
    expect(page.url()).toContain('/login');
    await context.close();
  });

  test('viewer制限 - マスタ管理', async ({ viewerPage }) => {
    await viewerPage.goto('/master-admin');
    // リダイレクトされるか、アクセス拒否メッセージが表示される
    const isRedirected = !viewerPage.url().includes('/master-admin');
    const isDenied = await viewerPage.getByText('管理者のみアクセス可能です。').isVisible().catch(() => false);
    expect(isRedirected || isDenied).toBeTruthy();
  });

  test('viewer制限 - 一括賃料改定', async ({ viewerPage }) => {
    await viewerPage.goto('/bulk-fee-update');
    await viewerPage.waitForLoadState('networkidle');
    const isRedirected = !viewerPage.url().includes('/bulk-fee-update');
    const isDenied = await viewerPage.getByText('管理者のみアクセス可能です。').isVisible().catch(() => false);
    expect(isRedirected || isDenied).toBeTruthy();
  });
});
