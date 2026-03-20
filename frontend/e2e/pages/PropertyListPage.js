import BasePage from './BasePage.js';

class PropertyListPage extends BasePage {
  constructor(page) {
    super(page);
    this.searchInput = page.getByPlaceholder('財産名・住所・地番で検索');
    this.typeFilter = page.locator('select').first();
    this.searchButton = page.getByRole('button', { name: '検索' });
    this.newButton = page.getByRole('button', { name: '新規登録' });
    this.heading = page.getByRole('heading', { name: '財産台帳一覧' });
  }

  async goto() {
    await this.navigate('/properties');
  }

  async search(query) {
    await this.searchInput.fill(query);
    await this.searchButton.click();
    await this.waitForLoad();
  }

  async filterByType(type) {
    await this.typeFilter.selectOption({ label: type });
    await this.waitForLoad();
  }

  async clickProperty(index = 0) {
    const row = this.page.locator('table tbody tr').nth(index);
    await row.click();
    await this.waitForLoad();
  }

  async clickNew() {
    await this.newButton.click();
    await this.waitForLoad();
  }

  async deleteProperty(index = 0) {
    // Set up confirm dialog handler
    this.page.once('dialog', async dialog => {
      await dialog.accept();
    });
    const deleteBtn = this.page.locator('table tbody tr').nth(index).getByRole('button', { name: '削除' });
    await deleteBtn.click();
    await this.waitForLoad();
  }

  async getRowCount() {
    return this.page.locator('table tbody tr').count();
  }

  async getTotal() {
    const text = await this.page.getByText(/ページ（全 \d+ 件）/).textContent();
    const match = text.match(/全 (\d+) 件/);
    return match ? parseInt(match[1], 10) : 0;
  }

  async goToPage(pageNum) {
    if (pageNum > 1) {
      await this.page.getByRole('button', { name: '次へ' }).click();
      await this.waitForLoad();
    }
  }

  isEmpty() {
    return this.page.getByText('財産データがありません').isVisible();
  }
}

export default PropertyListPage;
