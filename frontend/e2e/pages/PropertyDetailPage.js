import BasePage from './BasePage.js';

class PropertyDetailPage extends BasePage {
  constructor(page) {
    super(page);
  }

  async goto(id) {
    await this.navigate(`/properties/${id}`);
  }

  async getInfo() {
    const info = {};
    const labels = ['財産コード', '財産名称', '財産区分', '所在地', '地番', '地目', '面積（㎡）', '取得年月日', '備考'];
    for (const label of labels) {
      const row = this.page.getByText(label, { exact: true }).locator('..');
      const value = await row.locator('td').nth(1).textContent().catch(() => '');
      info[label] = value?.trim() || '';
    }
    return info;
  }

  async clickEdit() {
    await this.page.getByRole('button', { name: '編集' }).click();
    await this.waitForLoad();
  }

  async clickDelete() {
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    await this.page.getByRole('button', { name: '削除' }).click();
    await this.waitForLoad();
  }

  async switchTab(tabName) {
    await this.page.getByRole('button', { name: tabName, exact: true }).click();
    await this.waitForLoad();
  }

  async uploadFile(filePath) {
    const fileInput = this.page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    await this.waitForLoad();
  }

  async getFileCount() {
    // Switch to files tab first
    return this.page.locator('table tbody tr').count();
  }

  async getHistoryCount() {
    return this.page.locator('table tbody tr').count();
  }

  isNotFound() {
    return this.page.getByText('財産が見つかりません').isVisible();
  }
}

export default PropertyDetailPage;
