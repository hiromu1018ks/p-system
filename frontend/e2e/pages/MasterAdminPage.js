import BasePage from './BasePage.js';

class MasterAdminPage extends BasePage {
  constructor(page) {
    super(page);
  }

  async goto() {
    await this.navigate('/master-admin');
  }

  isAccessDenied() {
    return this.page.getByText('管理者のみアクセス可能です。').isVisible();
  }

  async switchTab(tabName) {
    await this.page.getByRole('button', { name: tabName, exact: true }).click();
    await this.waitForLoad();
  }

  // Unit Price
  async createUnitPrice(data) {
    await this.switchTab('単価マスタ');
    // Open form if not already open
    const newBtn = this.page.getByRole('button', { name: '新規登録' });
    if (await newBtn.isVisible()) {
      await newBtn.click();
    }
    if (data.property_sub_type) await this.page.getByLabel('財産種別').selectOption({ label: data.property_sub_type });
    if (data.usage) await this.page.getByPlaceholder('用途を入力').fill(data.usage);
    if (data.unit_price) await this.page.getByPlaceholder('0').first().fill(String(data.unit_price));
    if (data.effective_date) await this.page.getByLabel('適用開始日').fill(data.effective_date);
    await this.page.getByRole('button', { name: '登録' }).click();
    await this.waitForLoad();
  }

  async editUnitPrice(rowIndex, data) {
    // Click edit on specific row - implementation depends on UI
    // For now just navigate
  }

  // Users
  async createUser(data) {
    await this.switchTab('ユーザー管理');
    const newBtn = this.page.getByRole('button', { name: '新規ユーザー登録' });
    if (await newBtn.isVisible()) {
      await newBtn.click();
    }
    if (data.username) await this.page.getByPlaceholder('username').fill(data.username);
    if (data.password) await this.page.getByPlaceholder('パスワード').fill(data.password);
    if (data.display_name) await this.page.getByPlaceholder('田中太郎').fill(data.display_name);
    if (data.role) await this.page.getByLabel('権限').selectOption({ label: data.role });
    if (data.department) await this.page.getByPlaceholder('財政課').fill(data.department);
    await this.page.getByRole('button', { name: '登録' }).click();
    await this.waitForLoad();
  }

  async unlockUser(rowIndex = 0) {
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    await this.page.locator('table tbody tr').nth(rowIndex).getByRole('button', { name: 'ロック解除' }).click();
    await this.waitForLoad();
  }

  async getUserCount() {
    return this.page.locator('table tbody tr').count();
  }

  async getUnitPriceCount() {
    return this.page.locator('table tbody tr').count();
  }
}

export default MasterAdminPage;
