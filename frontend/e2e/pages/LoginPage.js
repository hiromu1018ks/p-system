import BasePage from './BasePage.js';

class LoginPage extends BasePage {
  constructor(page) {
    super(page);
    this.usernameInput = page.locator('#username');
    this.passwordInput = page.locator('#password');
    this.loginButton = page.getByRole('button', { name: 'ログイン' });
    this.heading = page.getByRole('heading', { name: 'ログイン' });
  }

  async goto() {
    await this.page.goto('/login');
    await this.waitForLoad();
  }

  async login(username, password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
    await this.page.waitForURL('**/dashboard');
    await this.waitForLoad();
  }

  async loginExpectError(username, password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    // Login failure returns 401, which client.js handles by redirecting to /login
    await this.loginButton.click();
    await this.page.waitForURL('**/login', { timeout: 10000 });
    return true;
  }

  async getErrorMessage() {
    const errorEl = this.page.locator('p').filter({ hasText: '' }).locator('visible=true').first();
    // Try to find error paragraph with red color
    try {
      const msg = await this.page.evaluate(() => {
        const ps = document.querySelectorAll('p');
        for (const p of ps) {
          if (p.style.color === 'red') return p.textContent;
        }
        return null;
      });
      return msg;
    } catch {
      return null;
    }
  }

  isLocked() {
    return this.page.getByText(/ロックされています|アカウントがロック/).isVisible();
  }
}
export default LoginPage;
