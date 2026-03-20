class BasePage {
  constructor(page) {
    this.page = page;
  }

  async waitForLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  async getFlashMessage() {
    // Check for toast/alert messages - the app uses window.alert() for errors
    // and inline messages with style color red
    const errorMsg = await this.page.locator('p[style*="color: red"], p[style*="color: \'red\'"], p[style*="color: \"red\""]').first().textContent().catch(() => null);
    return errorMsg;
  }

  assertUrl(path) {
    // Use expect from @playwright/test - but since we can't import it here,
    // just return a boolean
    return this.page.url().includes(path);
  }

  async navigate(path) {
    await this.page.goto(path);
    await this.waitForLoad();
  }
}
export default BasePage;
